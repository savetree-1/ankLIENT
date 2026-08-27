from playwright.sync_api import sync_playwright


with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(
        "http://127.0.0.1:9222"
    )

    chat_pages = []

    for context in browser.contexts:
        for page in context.pages:
            if page.url.startswith("https://chatgpt.com"):
                chat_pages.append(page)

    print(f"ChatGPT tabs found: {len(chat_pages)}")

    for i, page in enumerate(chat_pages):
        print(f"{i}: {page.url}")

    if not chat_pages:
        raise RuntimeError(
            "No ChatGPT tab found. Open https://chatgpt.com in the debug Edge."
        )

    page = chat_pages[0]

    print("\nUsing:")
    print(page.url)

    print("\nTitle:")
    print(page.title())
