"""
Take screenshots of each dashboard tab using Playwright.
"""

from playwright.sync_api import sync_playwright
import time

DASHBOARD = "file:///Users/pavelaverin/Desktop/LinkedIn Skill/mock_dashboard.html"
OUT_DIR = "/Users/pavelaverin/Desktop/LinkedIn Skill/screenshots"

TABS = [
    ("overview", "01-overview.png"),
    ("connections", "02-connections.png"),
    ("posts", "03-posts.png"),
    ("growth", "04-growth.png"),
    ("activity", "05-activity.png"),
    ("clusters", "06-clusters.png"),
]

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
    page.goto(DASHBOARD)
    page.wait_for_timeout(2000)  # Let Chart.js render

    for section_id, filename in TABS:
        # Click nav link
        page.click(f'nav a[data-section="{section_id}"]')
        page.wait_for_timeout(800)

        # For connections tab, add some sample filters to show the feature
        if section_id == "connections":
            # Add a seniority filter
            page.click("#connAddFilterBtn")
            page.wait_for_timeout(300)
            page.select_option("#connFilterType", "seniority")
            page.wait_for_timeout(200)
            page.select_option("#connFilterValue", "Director")
            page.click("#connApplyFilter")
            page.wait_for_timeout(300)
            # Add a company filter
            page.click("#connAddFilterBtn")
            page.wait_for_timeout(300)
            page.select_option("#connFilterType", "company")
            page.wait_for_timeout(200)
            page.select_option("#connFilterValue", "Google")
            page.click("#connApplyFilter")
            page.wait_for_timeout(500)

        # Screenshot the visible area
        page.screenshot(path=f"{OUT_DIR}/{filename}", full_page=False)
        print(f"Captured {filename}")

    browser.close()

print("All screenshots saved!")
