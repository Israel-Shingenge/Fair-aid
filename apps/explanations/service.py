"""
Orchestrates grounded explanations and follow-up conversations:

    stored engine result -> facts -> (cache) -> rate gate -> LLM -> validate -> response

* The engine's ``match_status`` is copied into every response by this code; the model only supplies prose.
* Prose that contradicts the engine (or invents numbers/links/promises) is discarded for the deterministic
  fallback, so an LLM failure can never change or block a pre-screening outcome.
* Hypothetical ("what if") questions: the model only translates the question into a change. The change is
  validated, the interpretable engine re-runs on it, and the answer is built from the engine's before/after.
"""
import dataclasses
import hashlib
import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from django.conf import settings

from apps.common.exceptions import NotFoundError
from apps.governance.safeguards import HumanInTheLoopPolicy
from apps.prescreening.adapters import profile_from_validated, scheme_to_criteria
from apps.prescreening.engine import evaluate_scheme
from apps.prescreening.models import PrescreenRecord
from apps.schemes.services import SchemeService

from .gate import RateGate
from .grounding import fallback, prompts, whatif
from .grounding.facts import SchemeFacts, facts_from_results, resolve_scheme
from .grounding.guardrails import validate_text
from .llm import LLMError, LLMRateLimited, active_model, get_llm_client, narrate_whatif_with_llm, provider
from .models import ConversationTurn, ExplanationCache

WHATIF_NOTE = "This is a what-if. Nothing was saved or submitted. Run the pre-screening again with your updated details for an official record."
MAX_STORED_TURNS = 50

@dataclass
class _Generated:
    payload: Optional[dict]
    source: str  # "llm" | "cache" | "fallback"
    reason: Optional[str] = None

def _cache_key(kind: str, facts: List[SchemeFacts], question: str = "", focus: Optional[str] = None,
               history: Optional[list] = None) -> str:
    blob = json.dumps(
        {
            "v": prompts.PROMPT_VERSION, "model": active_model(), "kind": kind,
            "facts": [f.for_prompt() for f in facts], "q": " ".join(question.lower().split()),
            "focus": focus, "hist": history or [],
        },
        sort_keys=True,
    )
    return hashlib.sha256(blob.encode()).hexdigest()

def _parse_json(text: str) -> Optional[dict]:
    try:
        data = json.loads(text)
    except ValueError:
        return None
    return data if isinstance(data, dict) else None

class ExplanationService:
    def __init__(self, gate: Optional[RateGate] = None, client_factory: Callable = get_llm_client):
        self.gate = gate or RateGate()
        self.client_factory = client_factory

    # ------------------------------------------------------------------ explain a whole run
    def explain_run(self, record: PrescreenRecord) -> Dict[str, Any]:
        facts = facts_from_results(record.results)
        generated = self._generate(
            _cache_key("explain", facts), "explain", prompts.explain_prompt(facts),
            parse=lambda text: self._parse_explain(text, facts), empty_ok=not facts,
        )
        llm_text = generated.payload or {}

        schemes = []
        for f in facts:
            text = llm_text.get(f.scheme_name)
            schemes.append(
                {
                    "scheme_name": f.scheme_name,
                    "match_status": f.match_status,  # from the engine, never from the model
                    "match_score": f.match_score,
                    "explanation": text or fallback.explain_scheme(f),
                    "source": generated.source if text else "fallback",
                }
            )
        overall_source = generated.source if any(s["source"] != "fallback" for s in schemes) else "fallback"
        return {
            "record_id": record.pk,
            "source": overall_source,
            "fallback_reason": generated.reason if overall_source == "fallback" else None,
            "overall_summary": fallback.overall_summary(facts),
            "schemes": schemes,
            "disclaimer": HumanInTheLoopPolicy.LEGAL_DISCLAIMER,
        }

    # ------------------------------------------------------------------ follow-up questions
    def answer_question(self, record: PrescreenRecord, question: str, scheme_name: Optional[str] = None) -> Dict[str, Any]:
        question = " ".join(question.split())
        facts = facts_from_results(record.results)
        focus = resolve_scheme(question, scheme_name, facts)
        if scheme_name and focus is None:
            raise NotFoundError(f"'{scheme_name}' was not part of this pre-screening run")

        history = self._history(record)
        context_text = question + " " + " ".join(f"{t['question']} {t['answer']}" for t in history)
        generated = self._generate(
            _cache_key("ask", facts, question, focus.scheme_name if focus else None, history), "ask",
            prompts.ask_prompt(facts, question, focus, history),
            parse=lambda text: self._parse_ask(text, facts, focus, context_text),
        )
        payload = generated.payload

        if payload and payload["intent"] == "what_if":
            out = self._answer_what_if(record, payload["changes"], question, context_text, focus, generated.source)
        elif payload:
            out = {"kind": "explanation", "answer": payload["answer"], "source": generated.source,
                   "fallback_reason": None, "what_if": None}
        else:
            answer = fallback.answer_about_scheme(focus) if focus else fallback.answer_general(facts)
            out = {"kind": "explanation", "answer": answer, "source": "fallback",
                   "fallback_reason": generated.reason, "what_if": None}

        turn = self._save_turn(record, question, out, focus)
        return {
            "record_id": record.pk,
            "turn_id": turn.pk,
            "question": question,
            "scheme_name": focus.scheme_name if focus else None,
            "match_status": focus.match_status if focus else None,  # authoritative, from the engine
            "disclaimer": HumanInTheLoopPolicy.LEGAL_DISCLAIMER,
            **out,
        }

    def conversation(self, record: PrescreenRecord) -> List[ConversationTurn]:
        return list(record.conversation_turns.all())

    def reset_conversation(self, record: PrescreenRecord) -> None:
        record.conversation_turns.all().delete()

    def quota_status(self) -> Dict[str, Any]:
        from .llm import llm_configured

        return {"enabled": llm_configured(), "provider": provider(), "model": active_model(), **self.gate.status()}

    # ------------------------------------------------------------------ what-if
    def _answer_what_if(self, record, changes, question, context_text, focus, interpretation_source) -> Dict[str, Any]:
        clean = whatif.validate_changes(changes, context_text)
        if clean is None:
            return {
                "kind": "explanation", "source": "fallback", "fallback_reason": "validation_failed", "what_if": None,
                "answer": fallback.answer_about_scheme(focus) if focus else
                "I couldn't turn that into a clear change I can check. Tell me the exact value, for example "
                "\"what if my household income were 200000?\". I can only test NQF level, household income, "
                "field of study or region.",
            }

        base = profile_from_validated(record.circumstances)
        hypothetical = whatif.apply_changes(base, clean)
        criteria = [scheme_to_criteria(s) for s in SchemeService.get_all_schemes()]
        before = {c.name: evaluate_scheme(base, c) for c in criteria}
        after = {c.name: evaluate_scheme(hypothetical, c) for c in criteria}
        diffs = [
            {
                "scheme_name": name,
                "before_status": before[name].match_status,
                "after_status": after[name].match_status,
                "changed": before[name].match_status != after[name].match_status,
            }
            for name in after
        ]
        description = whatif.describe(clean)
        answer, source, reason = fallback.whatif_answer(description, diffs, focus.scheme_name if focus else None), "engine", None

        if narrate_whatif_with_llm():
            after_facts = facts_from_results([dataclasses.asdict(r) for r in after.values()])
            prior = {d["scheme_name"]: d["before_status"] for d in diffs}
            focus_after = next((f for f in after_facts if focus and f.scheme_name == focus.scheme_name), None)
            narrated = self._generate(
                _cache_key("whatif", after_facts, json.dumps(clean, sort_keys=True) + " " + question,
                           focus.scheme_name if focus else None, [prior]),
                "whatif", prompts.whatif_prompt(clean, after_facts, prior, question),
                parse=lambda raw: self._parse_whatif_narration(raw, after_facts, focus_after, prior, context_text),
            )
            if narrated.payload:
                answer, source = narrated.payload["answer"], narrated.source
            else:
                reason = narrated.reason

        return {
            "kind": "what_if", "answer": answer, "source": source, "fallback_reason": reason,
            "what_if": {"hypothetical": True, "changes": clean, "schemes": diffs, "note": WHATIF_NOTE},
        }

    # ------------------------------------------------------------------ internals
    def _history(self, record: PrescreenRecord) -> List[Dict[str, str]]:
        limit = settings.LLM["HISTORY_TURNS"]
        if limit <= 0:
            return []
        turns = list(record.conversation_turns.order_by("-id")[:limit])
        return [{"question": t.question, "answer": t.answer} for t in reversed(turns)]

    def _save_turn(self, record: PrescreenRecord, question: str, out: dict, focus: Optional[SchemeFacts]) -> ConversationTurn:
        turn = ConversationTurn.objects.create(
            record=record, question=question, answer=out["answer"], kind=out["kind"],
            scheme_name=focus.scheme_name if focus else None, what_if=out["what_if"], source=out["source"],
        )
        stale = list(record.conversation_turns.order_by("-id").values_list("id", flat=True)[MAX_STORED_TURNS:])
        if stale:
            ConversationTurn.objects.filter(id__in=stale).delete()
        return turn

    def _generate(self, key: str, kind: str, prompt: str, parse: Callable[[str], Optional[dict]],
                  empty_ok: bool = False) -> _Generated:
        if empty_ok:
            return _Generated({}, "fallback", "nothing_to_explain")

        cached = ExplanationCache.objects.filter(key=key).first()
        if cached:
            return _Generated(cached.payload, "cache")

        client = self.client_factory()
        if client is None:
            return _Generated(None, "fallback", "disabled")

        permit = self.gate.acquire()
        if not permit.granted:
            return _Generated(None, "fallback", permit.reason)

        # Someone may have produced this exact answer while we queued for the slot: don't spend quota.
        cached = ExplanationCache.objects.filter(key=key).first()
        if cached:
            self.gate.release(permit, refund=True)
            return _Generated(cached.payload, "cache")

        try:
            raw = client.generate_json(prompts.SYSTEM_INSTRUCTION, prompt)
        except LLMRateLimited as exc:
            self.gate.block(exc.retry_after, exc.daily)
            self.gate.release(permit)
            return _Generated(None, "fallback", "daily_quota" if exc.daily else "rate_limited")
        except LLMError:
            self.gate.release(permit)
            return _Generated(None, "fallback", "llm_error")
        self.gate.release(permit)

        payload = parse(raw)
        if not payload:
            return _Generated(None, "fallback", "validation_failed")
        ExplanationCache.objects.update_or_create(
            key=key, defaults={"kind": kind, "payload": payload, "model": active_model()}
        )
        return _Generated(payload, "llm")

    @staticmethod
    def _parse_explain(raw: str, facts: List[SchemeFacts]) -> Optional[dict]:
        """Keep only per-scheme texts that pass validation; schemes without a valid text use the fallback."""
        data = _parse_json(raw)
        items = data.get("schemes") if data else None
        if not isinstance(items, list):
            return None
        by_name = {f.scheme_name: f for f in facts}
        accepted: Dict[str, str] = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            name, text = item.get("scheme_name"), item.get("explanation")
            if name in by_name and isinstance(text, str) and name not in accepted:
                if validate_text(text, facts, scope=by_name[name]).ok:
                    accepted[name] = text.strip()
        return accepted or None

    @staticmethod
    def _parse_ask(raw: str, facts: List[SchemeFacts], focus: Optional[SchemeFacts], context_text: str) -> Optional[dict]:
        data = _parse_json(raw)
        if not data:
            return None
        if data.get("intent") == "what_if":
            changes = data.get("changes")
            return {"intent": "what_if", "changes": changes} if isinstance(changes, dict) and changes else None
        answer = data.get("answer")  # "explain" / "out_of_scope" / a legacy reply without an intent
        if not isinstance(answer, str) or not validate_text(answer, facts, scope=focus, question=context_text).ok:
            return None
        return {"intent": "explain", "answer": answer.strip()}

    @staticmethod
    def _parse_whatif_narration(raw: str, after_facts: List[SchemeFacts], focus_after: Optional[SchemeFacts],
                                prior: Dict[str, str], context_text: str) -> Optional[dict]:
        data = _parse_json(raw)
        answer = data.get("answer") if data else None
        verdict = validate_text(answer, after_facts, scope=focus_after, question=context_text, prior_statuses=prior) \
            if isinstance(answer, str) else None
        return {"answer": answer.strip()} if verdict and verdict.ok else None
