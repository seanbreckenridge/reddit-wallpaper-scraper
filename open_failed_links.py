import webbrowser

with open("failed.txt") as f:
    open_five_links = 5
    for url in f:
        open_five_links -= 1
        webbrowser.open_new_tab(url.strip())
        if open_five_links == 0:
            open_five_links = 5
            input("Hit enter to open 5 more links...")
