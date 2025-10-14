"""Performance benchmarks for Nova backend."""

import asyncio
import time
import os
from statistics import mean, stdev
from dotenv import load_dotenv

from src.community_bot.config import load_settings
from src.community_bot.agent_client import AgentClient
from src.community_bot.logging_config import setup_logging


async def benchmark_nova():
    """Benchmark Nova response times."""
    load_dotenv()
    
    # Override to use Nova
    os.environ["BACKEND_MODE"] = "nova"
    
    settings = load_settings()
    setup_logging("INFO")
    
    client = AgentClient(settings)
    
    # Test queries of varying complexity
    queries = [
        "What is AI?",
        "Explain the concept of machine learning in one paragraph.",
        "What is Python?",
        "Tell me about AWS Bedrock.",
        "What are the benefits of cloud computing?",
    ]
    
    response_times = []
    token_counts = []
    
    print("=" * 80)
    print("Nova Performance Benchmark")
    print("=" * 80)
    
    for i, query in enumerate(queries, 1):
        print(f"\nTest {i}/{len(queries)}: {query}")
        print("-" * 40)
        
        start_time = time.time()
        first_chunk_time = None
        response = ""
        chunk_count = 0
        
        async for chunk in client.chat(query):
            if first_chunk_time is None:
                first_chunk_time = time.time()
            response += chunk
            chunk_count += 1
        
        end_time = time.time()
        
        total_time = end_time - start_time
        ttft = first_chunk_time - start_time if first_chunk_time else 0
        
        response_times.append(total_time)
        
        # Rough token count (4 chars per token average)
        approx_tokens = len(response) // 4
        token_counts.append(approx_tokens)
        
        print(f"Response: {len(response)} chars (~{approx_tokens} tokens)")
        print(f"Total time: {total_time:.2f}s")
        print(f"Time to first token: {ttft:.2f}s")
        print(f"Chunks received: {chunk_count}")
        if total_time > 0:
            print(f"Throughput: ~{approx_tokens/total_time:.1f} tokens/sec")
    
    print("\n" + "=" * 80)
    print("Statistics:")
    print("=" * 80)
    print(f"Mean response time: {mean(response_times):.2f}s")
    print(f"Std dev: {stdev(response_times):.2f}s" if len(response_times) > 1 else "N/A")
    print(f"Min: {min(response_times):.2f}s")
    print(f"Max: {max(response_times):.2f}s")
    print(f"\nMean tokens: ~{mean(token_counts):.0f}")
    print(f"Total tokens: ~{sum(token_counts)}")
    
    # Cost estimate (Nova-Pro pricing)
    input_cost = sum([len(q) // 4 for q in queries]) * 0.80 / 1_000_000
    output_cost = sum(token_counts) * 3.20 / 1_000_000
    total_cost = input_cost + output_cost
    
    print(f"\nEstimated cost for this test:")
    print(f"Input: ${input_cost:.6f}")
    print(f"Output: ${output_cost:.6f}")
    print(f"Total: ${total_cost:.6f}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(benchmark_nova())
