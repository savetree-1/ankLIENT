from app.browser.recovery import recover_connection

conn, page = recover_connection("http://127.0.0.1:9222")

img = page.page.locator('img[alt^="Generated image"]').first
if img.count() > 0:
    src = img.get_attribute("src")
    print(f"Downloading {src[:50]}...")
    resp = page.page.request.get(src)
    print(resp.status)
    with open("test.png", "wb") as f:
        f.write(resp.body())
    print("Saved test.png")
else:
    print("No image found.")
