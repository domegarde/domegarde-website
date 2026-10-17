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

## Two more pages written the same way

- **Domegarde in brief** (`facts.html` / `en-bref.html`) comes from `page-facts.en.md` and `page-facts.fr.md`. Keep it in step with the pricing page and "What's coming": it is the page people and AI systems quote. Change `updated:` whenever you change it. The `features:` list at the top feeds the structured data.
- **What's new** (`whats-new.html` / `nouveautes.html`) comes from `page-changelog.en.md` and `page-changelog.fr.md`. Add a new entry **at the top** of both files, in the same shape:

      ## 2026-11-03 | Short title | Product
      - One line on what changed for the landlord.

  The tag is `Product` (French `Produit`) for the app or `Website` (`Site`) for this site. Use the day the change went live. Also change `updated:` at the top.

Run `python3 tools/build-blog.py` after any change to these files.

## Draft pages and placeholders (the scaffolds)

Pages that are written but not ready for the public are **drafts**. Put `status: draft` in the front matter of a `page-<name>.<lang>.md` file (posts already work this way). A draft:

- shows a yellow box at the top with its `review:` checklist and a count of its placeholders;
- is always `noindex`, whatever `NOINDEX` says, and is never in the sitemap or the feeds;
- is not linked from the header, the footer or any live page. The only list of drafts is the internal page **Drafts to review** (`review.html`, French `a-relire.html`), which is built automatically.

A **placeholder** marks where content goes. It is a block of plain lines, with no blank line inside:

    :::placeholder A short title
    What goes here: what this part of the page is for, in a sentence or two.
    Suggestion:
    - one idea for what to write
    - another idea
    Needs: who has to provide it (French: "Ce qui va ici :", "Suggestion :", "À fournir :")
    :::

It appears as a dashed numbered box (Placeholder 1, 2, 3 and so on). Replace the whole block with the real text when you have it. Extra front matter for pages: `reviewer:` (shown on the review page) and `internal: yes` (for the review page itself).

**Obligation pages:** `page-ob-<name>.en.md` and `.fr.md`, one per legal duty (44, generated once from the app's catalogue, now edited by hand). They need `stage:` (0 to 5), `tier:` (stops, money, dispute or practice) and `order:` in the front matter. They are listed by `page-obligations.*.md` (the line `{{obligation-list}}`).

### Publishing a draft

1. Replace every placeholder with the real text, and clear the review list: each point checked, or removed with the reason.
2. Remove `status: draft` in both languages.
3. Run `python3 tools/build-blog.py` (it adds the page to the sitemap on its own).
4. Add the link where it belongs (footer, About page, or the app), and add an entry to `page-changelog.*.md`.
5. On launch day only: set `NOINDEX = False`. Drafts stay hidden regardless.

