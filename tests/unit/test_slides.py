from __future__ import annotations

from vaultpub.core.config import PublisherConfig
from vaultpub.core.index import VaultIndexer
from vaultpub.core.render import Renderer
from vaultpub.core.render.slides import (
    SlideOptions,
    collect_directory_notes,
    collect_slide_scope_directories,
    segment_slides,
    slide_options,
    slide_split_override,
    validated_slide_deck_order,
)
from vaultpub.core.render.templates import multi_note_slide_sections_html


def test_explicit_separators_override_heading_splitting() -> None:
    segmented = segment_slides("# Title\n\n## First\n\nText\n\n---\n\n## Second\n\nText\n")

    assert segmented.mode == "explicit"
    assert len(segmented.fragments) == 2
    assert "## First" in segmented.fragments[0]
    assert "## Second" in segmented.fragments[1]


def test_auto_h2_splitting_keeps_h3_with_parent() -> None:
    segmented = segment_slides("# Title\n\nIntro\n\n## A\n\n### Detail\n\nText\n\n## B\n\nText\n")

    assert segmented.mode == "headings"
    assert len(segmented.fragments) == 3
    assert "# Title" in segmented.fragments[0]
    assert "### Detail" in segmented.fragments[1]
    assert "## B" in segmented.fragments[2]


def test_auto_h2_splitting_allows_missing_h1() -> None:
    segmented = segment_slides("Intro\n\n## A\n\nText\n\n## B\n\nText\n")

    assert segmented.mode == "headings"
    assert len(segmented.fragments) == 3
    assert segmented.fragments[0].startswith("Intro")


def test_single_slide_fallback_without_h2() -> None:
    segmented = segment_slides("# Title\n\nLong text\n")

    assert segmented.mode == "single"
    assert segmented.fragments == ("# Title\n\nLong text\n",)


def test_manual_split_policies_are_predictable_and_keep_rules_when_not_explicit() -> None:
    source = "# Title\n\n---\n\n## Topic\n\n### Detail\n\n# Next\n"

    assert segment_slides(source, "explicit").mode == "explicit"
    assert len(segment_slides(source, "h1").fragments) == 2
    assert len(segment_slides(source, "h2").fragments) == 2
    assert len(segment_slides(source, "h3").fragments) == 2
    assert segment_slides(source, "single").fragments == (source,)
    assert segment_slides(source, "h2").mode == "explicit"
    assert "---" not in segment_slides(source, "h2").fragments[0]


def test_named_split_policies_route_to_their_semantic_heading_levels() -> None:
    source = "# Chapter\n\n## Section\n\n### Detail\n\nText\n\n# Next chapter\n"

    assert len(segment_slides(source, "chapters").fragments) == 2
    assert len(segment_slides(source, "sections").fragments) == 2
    assert len(segment_slides(source, "detail").fragments) == 3
    assert len(segment_slides(source, "fit").fragments) == 2
    assert segment_slides(source, "explicit").fragments == (source,)
    assert segment_slides(source, "single").fragments == (source,)


def test_reveal_only_theme_falls_back_to_light() -> None:
    assert slide_options({"slide": {"theme": "white"}}).theme == "light"
    assert slide_options({"slide": {"theme": "moon"}}).theme == "light"
    assert slide_options({"slide": {"theme": "dracula"}}).theme == "dracula"


def test_controls_are_always_disabled_and_split_overrides_are_validated() -> None:
    assert slide_options({"slide": {"controls": True}}).controls is False
    assert slide_split_override("fit", "single") == "fit"
    assert slide_split_override("detail", "single") == "detail"
    assert slide_split_override("white", "single") == "single"


def test_frontmatter_comments_and_fenced_separators_do_not_split() -> None:
    segmented = segment_slides(
        "---\nslide:\n  theme: white\n---\n\n# Example\n\n%%\n---\n%%\n\n```yaml\n---\nfoo: bar\n---\n```\n\n## Next\n"
    )

    assert segmented.mode == "headings"
    assert len(segmented.fragments) == 2
    assert "foo: bar" in segmented.fragments[0]


def test_tilde_fence_separator_does_not_enable_explicit_mode() -> None:
    segmented = segment_slides("# Example\n\n~~~yaml\n---\n~~~\n\n## Next\n")

    assert segmented.mode == "headings"
    assert len(segmented.fragments) == 2


def test_setext_headings_and_empty_explicit_fragments_are_not_slide_boundaries() -> None:
    setext = segment_slides("Title\n---\n\n## Section\n\nText\n")
    explicit = segment_slides("# A\n\n---\n\n---\n\n# B\n\n---\n")
    empty = segment_slides("")

    assert setext.mode == "headings"
    assert setext.fragments[0] == "Title\n---\n"
    assert explicit.mode == "explicit"
    assert explicit.fragments == ("# A\n", "# B\n")
    assert empty == type(empty)(mode="single", fragments=("",))


def test_slide_options_are_allowlisted() -> None:
    options = slide_options(
        {
            "slide": {
                "theme": "dracula",
                "transition": "zoom",
                "controls": False,
                "progress": "yes",
                "slideNumber": False,
                "center": False,
                "width": 1920,
                "height": -1,
                "hash": False,
                "split": "h3",
                "codeWrap": False,
                "plugins": "unsafe",
            }
        }
    )

    assert options == SlideOptions(
        theme="dracula",
        transition="zoom",
        controls=False,
        progress=True,
        slide_number=False,
        center=False,
        width=1920,
        height=900,
        hash=False,
        split="h3",
        code_wrap=False,
    )


def test_slide_split_override_prefers_valid_query_then_valid_cookie() -> None:
    assert slide_split_override("h1", "single") == "h1"
    assert slide_split_override("invalid", "single") == "single"
    assert slide_split_override(None, "invalid") is None


def test_slide_deck_orders_match_navigation_rules_and_ignore_hidden_nodes(tmp_path) -> None:
    (tmp_path / "Folder").mkdir()
    (tmp_path / "A.md").write_text("# A\n", encoding="utf-8")
    (tmp_path / "B.md").write_text("# B\n", encoding="utf-8")
    (tmp_path / "D.md").write_text("# D\n", encoding="utf-8")
    (tmp_path / "Folder" / "C.md").write_text("# C\n", encoding="utf-8")
    (tmp_path / "__order__.json").write_text('["B.md", "Folder/", "A.md"]', encoding="utf-8")
    index = VaultIndexer(PublisherConfig(vault_path=tmp_path)).build()

    assert index.nav_tree is not None
    root = index.nav_tree
    by_path = {child.path: child for child in root.children}
    by_path["A.md"].starred = True
    by_path["A.md"].created_ns = 1
    by_path["B.md"].created_ns = 10
    by_path["D.md"].created_ns = 3
    by_path["Folder"].created_ns = 5
    by_path["A.md"].modified_ns = 1
    by_path["B.md"].modified_ns = 10
    by_path["D.md"].modified_ns = 3
    by_path["Folder"].modified_ns = 5

    paths = lambda order: [note.rel_path.as_posix() for note in collect_directory_notes(root, index, order)]
    assert paths("predefined") == ["A.md", "B.md", "Folder/C.md", "D.md"]
    assert paths("modified-desc") == ["A.md", "B.md", "Folder/C.md", "D.md"]
    assert paths("name-asc") == ["A.md", "Folder/C.md", "B.md", "D.md"]
    assert paths("name-desc") == ["A.md", "Folder/C.md", "D.md", "B.md"]
    assert paths("created-desc") == ["A.md", "Folder/C.md", "B.md", "D.md"]
    assert paths("created-asc") == ["A.md", "Folder/C.md", "D.md", "B.md"]

    by_path["B.md"].nav_hidden = True
    assert paths("predefined") == ["A.md", "Folder/C.md", "D.md"]
    assert validated_slide_deck_order("name-asc") == "name-asc"
    assert validated_slide_deck_order("unknown") is None


def test_slide_scope_directories_and_note_dividers_are_safe(tmp_path) -> None:
    (tmp_path / "Course" / "Nested").mkdir(parents=True)
    (tmp_path / "Empty").mkdir()
    (tmp_path / "Course" / "Nested" / "One.md").write_text("# One\n", encoding="utf-8")
    (tmp_path / "Course" / "Two.md").write_text("---\ntitle: <Unsafe>\n---\n# Two\n", encoding="utf-8")
    index = VaultIndexer(PublisherConfig(vault_path=tmp_path)).build()

    assert index.nav_tree is not None
    scopes = collect_slide_scope_directories(index.nav_tree, index)
    assert [scope.path for scope in scopes] == ["Course", "Course/Nested"]
    note = index.notes_by_id[index.notes_by_path["Course/Two.md"]]
    slides = Renderer(PublisherConfig(vault_path=tmp_path), index).render_slides(note)
    html = multi_note_slide_sections_html([(note, slides)])

    assert html.count("<section") == 2
    assert 'data-slide-kind="note-divider"' in html
    assert "&lt;Unsafe&gt;" in html
    assert "Course/Two.md" in html


def test_renderer_renders_later_slide_links_embeds_and_heading_ids(tmp_path) -> None:
    (tmp_path / "Folder").mkdir()
    (tmp_path / "Folder" / "image.png").write_bytes(b"image")
    (tmp_path / "Target.md").write_text("# Target\n", encoding="utf-8")
    (tmp_path / "Folder" / "Note.md").write_text(
        "# Title\n\nIntro\n\n## Second\n\n[[Target]]\n\n![[image.png]]\n",
        encoding="utf-8",
    )
    index = VaultIndexer(PublisherConfig(vault_path=tmp_path)).build()
    note = index.notes_by_id[index.notes_by_path["Folder/Note.md"]]

    slides = Renderer(PublisherConfig(vault_path=tmp_path), index).render_slides(note)

    assert len(slides) == 2
    assert 'id="title"' in slides[0].html
    assert 'id="second"' in slides[1].html
    assert 'href="/Target.md"' in slides[1].html
    assert 'src="/assets/Folder/image.png"' in slides[1].html


def test_renderer_preserves_supported_content_and_does_not_split_embedded_note(tmp_path) -> None:
    (tmp_path / "Parent.md").write_text(
        "# Parent\n\n![[Embedded]]\n\n## Content\n\n> [!note] Callout\n> Text\n\n```mermaid\ngraph TD\nA --> B\n```\n\n```python\nprint('code')\n```\n\n| A | B |\n| - | - |\n| 1 | 2 |\n\n$E = mc^2$\n\n[External](https://example.com)\n\n<script>alert(1)</script>\n",
        encoding="utf-8",
    )
    (tmp_path / "Embedded.md").write_text("# Embedded\n\n---\n\n# Still embedded\n", encoding="utf-8")
    index = VaultIndexer(PublisherConfig(vault_path=tmp_path)).build()
    note = index.notes_by_id[index.notes_by_path["Parent.md"]]

    slides = Renderer(PublisherConfig(vault_path=tmp_path), index).render_slides(note)

    assert len(slides) == 2
    assert 'class="embed-wrapper"' in slides[0].html
    assert 'class="callout"' in slides[1].html
    assert 'class="mermaid"' in slides[1].html
    assert 'class="math inline"' in slides[1].html
    assert 'language-python' in slides[1].html
    assert "<table>" in slides[1].html
    assert 'href="https://example.com"' in slides[1].html
    assert "<script" not in slides[1].html


def test_folder_slide_heading_namespaces_cover_later_slide_hash_links(tmp_path) -> None:
    (tmp_path / "First.md").write_text(
        "# First\n\n[[#Shared]]\n\n[Markdown link](#Shared)\n\n## Shared\n\nFirst content\n",
        encoding="utf-8",
    )
    (tmp_path / "Second.md").write_text("# Second\n\n## Shared\n\nSecond content\n", encoding="utf-8")
    index = VaultIndexer(PublisherConfig(vault_path=tmp_path)).build()
    renderer = Renderer(PublisherConfig(vault_path=tmp_path), index)
    first = index.notes_by_id[index.notes_by_path["First.md"]]
    second = index.notes_by_id[index.notes_by_path["Second.md"]]

    first_slides = renderer.render_slides(first, heading_namespace="first")
    second_slides = renderer.render_slides(second, heading_namespace="second")

    assert 'href="#first-shared"' in first_slides[0].html
    assert 'id="first-shared"' in first_slides[1].html
    assert 'id="second-shared"' in second_slides[1].html


def test_directory_notes_follow_visible_navigation_order(tmp_path) -> None:
    (tmp_path / "Nested").mkdir()
    (tmp_path / "A.md").write_text("# A\n", encoding="utf-8")
    (tmp_path / "B.md").write_text("# B\n", encoding="utf-8")
    (tmp_path / "Nested" / "C.md").write_text("# C\n", encoding="utf-8")
    (tmp_path / "__order__.json").write_text('["B.md", "Nested/", "A.md"]', encoding="utf-8")
    index = VaultIndexer(PublisherConfig(vault_path=tmp_path)).build()

    assert index.nav_tree is not None
    assert [note.rel_path.as_posix() for note in collect_directory_notes(index.nav_tree, index)] == [
        "B.md",
        "Nested/C.md",
        "A.md",
    ]
