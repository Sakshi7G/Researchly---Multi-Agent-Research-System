from agents import build_search_agent, writer_chain, critic_chain
from tools import scrape_url


def run_research_pipeline(topic: str) -> dict:

    state = {}

    # Step 1 - Search Agent
    print("\n" + " =" * 50)
    print("step 1 - Search agent is working ...")
    print("=" * 50)

    search_agent = build_search_agent()

    search_result = search_agent.invoke({
        "messages": [
            (
                "user",
                f"Find recent, reliable and detailed information about: {topic}"
            )
        ]
    })

    state["search_results"] = search_result["messages"][-1].content

    print("\nsearch result\n", state["search_results"])


    # Step 2 - Scrape search results directly
    print("\n" + " =" * 50)
    print("step 2 - Scraping top resource ...")
    print("=" * 50)

    # Extract the first URL from the search results
    import re

    urls = re.findall(r"https?://[^\s>|]+", state["search_results"])

    if urls:
        url = urls[0].rstrip(").,")
        print("\nScraping URL:", url)

        state["scraped_content"] = scrape_url.invoke(url)

    else:
        state["scraped_content"] = "No URL found in search results."

    print("\nScraped content:\n", state["scraped_content"])


    # Step 3 - Writer
    print("\n" + " =" * 50)
    print("step 3 - Writer is drafting the report ...")
    print("=" * 50)

    research_combined = (
        f"SEARCH RESULTS:\n{state['search_results']}\n\n"
        f"DETAILED SCRAPED CONTENT:\n{state['scraped_content']}"
    )

    state["report"] = writer_chain.invoke({
        "topic": topic,
        "research": research_combined
    })

    print("\nFinal Report\n", state["report"])


    # Step 4 - Critic
    print("\n" + " =" * 50)
    print("step 4 - Critic is reviewing the report ...")
    print("=" * 50)

    state["feedback"] = critic_chain.invoke({
        "report": state["report"]
    })

    print("\nCritic Report\n", state["feedback"])

    return state


if __name__ == "__main__":
    topic = input("\nEnter a research topic: ")
    run_research_pipeline(topic)