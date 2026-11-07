
import asyncio


def test_scheduler_respects_concurrency_limit():
    async def run_test():
        semaphore = asyncio.Semaphore(2)
        active = 0
        maximum_active = 0

        async def worker():
            nonlocal active, maximum_active

            async with semaphore:
                active += 1
                maximum_active = max(maximum_active, active)
                await asyncio.sleep(0.01)
                active -= 1

        await asyncio.gather(*(worker() for _ in range(6)))

        assert maximum_active == 2

    asyncio.run(run_test())


def test_scheduler_continues_after_task_failure():
    async def run_test():
        async def worker(task_id):
            if task_id == "task-2":
                raise RuntimeError("Expected failure")
            return task_id

        results = await asyncio.gather(
            worker("task-1"),
            worker("task-2"),
            worker("task-3"),
            return_exceptions=True,
        )

        assert results[0] == "task-1"
        assert isinstance(results[1], RuntimeError)
        assert results[2] == "task-3"

    asyncio.run(run_test())
