def normalize_link(link, base_url):
    return base_url + link if link.startswith('/') else link
