# Writing a blog post

Each post is two small text files, one per language, in this folder:

    2026-11-03-my-slug.en.md
    2026-11-03-my-slug.fr.md

The date and the slug (the middle part) must be the same in both files. The date is the publication date.

## What goes at the top

    ---
    title: The headline
    section: building          (building = "Building Domegarde", news = "French property news")
    status: draft              (draft shows a yellow review banner; delete this line to publish)
    author: The Domegarde team (optional; this is the default)
    checked: 2026-11-03        (news posts only: the day you last checked the facts)
    excerpt: One or two sentences shown on the blog page and in search results.
    review:                    (draft only: a list of things to check before publishing)
    - First thing to check
    sources:                   (news posts: every official or press source, one per line)
    - Name of the source | https://the-link
    ---

Then the post itself. Use `## Heading` for sections, `- ` for bullet lists, `**bold**`, `*italic*` and `[link text](https://link)`.

## Rules for the news section

1. Every claim links to a source. Prefer official ones (Légifrance, service-public.fr, ecologie.gouv.fr, ANIL, impots.gouv.fr) over press.
2. Say what the text says. No advice, and say plainly what we do not know.
3. Put the date you checked in `checked:`. Rules change: re-check, update or retire old posts.
4. Someone other than the writer reads it before it goes out (Claudia for the French; a lawyer or ADIL for the substance when we have one).

## Publishing

While the website is private every page carries a `noindex` line. The blog builder writes it too (`NOINDEX = True` at the top of `tools/build-blog.py`); on launch day change it to `False` and rebuild.

Run `python3 tools/build-blog.py` from the website folder. It rebuilds `blog.html`, `blog-fr.html`, every post page and the two RSS feeds. Then commit the new files as usual.
