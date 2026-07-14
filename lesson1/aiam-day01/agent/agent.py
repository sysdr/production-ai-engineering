import time
import logging
from agent.core.types import AgentRequest, AgentResponse, SecurityContext
from agent.core.metrics import METRICS
from agent.layers.security import SecurityPerimeter
from agent.layers.memory import InMemoryStore
from agent.layers.tool_orchestrator import ToolOrchestrator
from agent.layers.llm import CoreLLM

log = logging.getLogger("agent")


class SecureAgent:
    """
    The 4-layer secure agent.
    Request flows:  Input → L4 → L3 → L2 → L1
    Response flows: L1 → L2 (store) → L3 (filter) → Output
    """

    def __init__(self):
        self.security = SecurityPerimeter()
        self.tools = ToolOrchestrator()
        self.memory = InMemoryStore()
        self.llm = CoreLLM()

    def run(
        self, raw_input: str, ctx: SecurityContext, *, label: str = ""
    ) -> AgentResponse:
        t0 = time.perf_counter()
        request = AgentRequest(raw_input=raw_input, security_ctx=ctx)

        try:
            ts = time.perf_counter()
            request = self.security.process(request)
            l4_ms = max(1, int((time.perf_counter() - ts) * 1000))

            self.tools.get_available_tools(ctx.permissions)

            ts = time.perf_counter()
            history = self.memory.get_context(ctx.session_id)
            l2_ms = max(1, int((time.perf_counter() - ts) * 1000))

            messages = history + [{"role": "user", "content": request.raw_input}]
            ts = time.perf_counter()
            response = self.llm.call(request, messages)
            l1_ms = max(1, int((time.perf_counter() - ts) * 1000))

            self.memory.store(ctx.session_id, raw_input, response.content)
            response = self.tools.filter_output(response)

            response.layer_timings = {
                "l4_security_ms": l4_ms,
                "l2_memory_ms": l2_ms,
                "l1_llm_ms": l1_ms,
                "total_ms": max(1, int((time.perf_counter() - t0) * 1000)),
            }
            response.status = "ok"
            METRICS.record(
                status="ok",
                tokens=response.tokens_used,
                cost_usd=response.cost_usd,
                latency_ms=response.latency_ms,
                layer_timings=response.layer_timings,
                content=response.content,
                label=label or "ok",
            )
            log.info(
                f"[AGENT] complete — request_id={response.request_id} "
                f"total={response.layer_timings['total_ms']}ms "
                f"cost=${response.cost_usd}"
            )
            return response

        except PermissionError as e:
            timings = {"total_ms": max(1, int((time.perf_counter() - t0) * 1000))}
            METRICS.record(
                status="blocked",
                latency_ms=timings["total_ms"],
                layer_timings=timings,
                content=str(e),
                label=label or "blocked",
            )
            raise
        except ValueError as e:
            timings = {"total_ms": max(1, int((time.perf_counter() - t0) * 1000))}
            METRICS.record(
                status="rejected",
                latency_ms=timings["total_ms"],
                layer_timings=timings,
                content=str(e),
                label=label or "rejected",
            )
            raise
