from app.browser.recovery import recover_connection

conn, page = recover_connection("http://127.0.0.1:9222")

img = page.page.locator('img[alt^="Generated image"]').first
if img.count() > 0:
    print(img.evaluate("""
        element => {
            let curr = element.parentElement;
            let path = [];
            while(curr && curr.tagName !== 'BODY') {
                path.push(curr.tagName + (curr.className ? '.' + curr.className.split(' ').join('.') : ''));
                curr = curr.parentElement;
            }
            return path;
        }
    """))
