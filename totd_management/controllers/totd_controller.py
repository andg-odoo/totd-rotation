# -*- coding: utf-8 -*-
from odoo import http


class totdController(http.Controller):
    @http.route("/totd", type="http", auth="public", website=True)
    def books(self, **kwargs):
        # checked_out_books = (
        #     http.request.env["library.rental"].search([]).rented_books_ids
        # )
        # available_books = http.request.env["library.copies"].search(
        #     [("id", "not in", checked_out_books.ids)]
        # )
        return http.request.render(
            "library_management.books_website",
            {"totd": available_books},
        )
