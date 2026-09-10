from django.template.loader import render_to_string


class TestEmailFooter:
    def test_disclaimer_always_present(self):
        rendered = render_to_string("notifications/_email_footer.html", {})
        assert "not personalised investment advice" in rendered

    def test_legal_block_hidden_when_empty(self):
        rendered = render_to_string(
            "notifications/_email_footer.html",
            {
                "legal_entity_name": "",
                "legal_entity_address": "",
                "cif_registration_number": "",
                "orias_number": "",
            },
        )
        assert "CIF registration" not in rendered

    def test_legal_block_shown_once_populated(self):
        rendered = render_to_string(
            "notifications/_email_footer.html",
            {
                "legal_entity_name": "Portfolio App SAS",
                "legal_entity_address": "1 rue Example, Paris",
                "cif_registration_number": "CIF-12345",
                "orias_number": "ORIAS-6789",
            },
        )
        assert "Portfolio App SAS" in rendered
        assert "CIF-12345" in rendered
        assert "ORIAS-6789" in rendered

    def test_unsubscribe_link_only_when_url_given(self):
        without = render_to_string("notifications/_email_footer.html", {})
        with_link = render_to_string(
            "notifications/_email_footer.html",
            {"unsubscribe_url": "https://example.invalid/u/token"},
        )
        assert "Unsubscribe" not in without
        assert "https://example.invalid/u/token" in with_link


class TestEmailBasePlainTextAlternative:
    def test_txt_and_html_base_both_include_disclaimer(self):
        html = render_to_string("notifications/email_base.html", {})
        text = render_to_string("notifications/email_base.txt", {})
        assert "not personalised investment advice" in html
        assert "not personalised investment advice" in text
