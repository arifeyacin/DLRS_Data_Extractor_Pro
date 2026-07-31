"""
Search Tab Module for DLRS Data Extractor Pro Desktop GUI
Provides structured filter fields, FTS5 keyword search, and tabular query results.
"""

import customtkinter as ctk
from typing import Callable, Optional, List, Dict, Any

class SearchTab(ctk.CTkFrame):
    """Full-Text and Structured Database Search View."""

    def __init__(self, master, on_search: Callable[..., List[Dict[str, Any]]], on_export: Callable[[], None]):
        super().__init__(master, corner_radius=10)
        self.on_search_cb = on_search
        self.on_export_cb = on_export
        self.results_data: List[Dict[str, Any]] = []

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        # 1. Header
        lbl_title = ctk.CTkLabel(
            self,
            text="Land Records Search & Explorer",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold")
        )
        lbl_title.pack(anchor="w", padx=20, pady=(15, 5))

        # 2. Filter Inputs Grid
        filter_frame = ctk.CTkFrame(self, corner_radius=8)
        filter_frame.pack(fill="x", padx=20, pady=10)
        filter_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Row 1: Keyword & District
        ctk.CTkLabel(filter_frame, text="Keyword (FTS5):", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=0, padx=10, pady=(10, 2), sticky="w")
        self.entry_keyword = ctk.CTkEntry(filter_frame, placeholder_text="Search any text...")
        self.entry_keyword.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(filter_frame, text="District (জেলা):", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=1, padx=10, pady=(10, 2), sticky="w")
        self.entry_district = ctk.CTkEntry(filter_frame, placeholder_text="e.g. ঢাকা")
        self.entry_district.grid(row=1, column=1, padx=10, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(filter_frame, text="Upazila (উপজেলা):", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=2, padx=10, pady=(10, 2), sticky="w")
        self.entry_upazila = ctk.CTkEntry(filter_frame, placeholder_text="e.g. ডেমরা")
        self.entry_upazila.grid(row=1, column=2, padx=10, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(filter_frame, text="Mouza (মৌজা):", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=3, padx=10, pady=(10, 2), sticky="w")
        self.entry_mouza = ctk.CTkEntry(filter_frame, placeholder_text="e.g. ডেমরা")
        self.entry_mouza.grid(row=1, column=3, padx=10, pady=(0, 10), sticky="ew")

        # Row 2: Owner, Khatian, Dag
        ctk.CTkLabel(filter_frame, text="Owner Name (মালিক):", font=ctk.CTkFont(size=11, weight="bold")).grid(row=2, column=0, padx=10, pady=(5, 2), sticky="w")
        self.entry_owner = ctk.CTkEntry(filter_frame, placeholder_text="e.g. আব্দুল")
        self.entry_owner.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(filter_frame, text="Khatian (খতিয়ান):", font=ctk.CTkFont(size=11, weight="bold")).grid(row=2, column=1, padx=10, pady=(5, 2), sticky="w")
        self.entry_khatian = ctk.CTkEntry(filter_frame, placeholder_text="e.g. ১০৪২")
        self.entry_khatian.grid(row=3, column=1, padx=10, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(filter_frame, text="Dag (দাগ):", font=ctk.CTkFont(size=11, weight="bold")).grid(row=2, column=2, padx=10, pady=(5, 2), sticky="w")
        self.entry_dag = ctk.CTkEntry(filter_frame, placeholder_text="e.g. ৫১২")
        self.entry_dag.grid(row=3, column=2, padx=10, pady=(0, 10), sticky="ew")

        # Action Buttons
        btn_box = ctk.CTkFrame(filter_frame, fg_color="transparent")
        btn_box.grid(row=3, column=3, padx=10, pady=(0, 10), sticky="ew")

        btn_search = ctk.CTkButton(btn_box, text="🔍 Search", fg_color="#00A63E", hover_color="#008532", command=self._execute_search)
        btn_search.pack(side="left", expand=True, fill="x", padx=(0, 4))

        btn_export = ctk.CTkButton(btn_box, text="💾 Export Results", fg_color="#1568B2", hover_color="#104E85", command=self.on_export_cb)
        btn_export.pack(side="left", expand=True, fill="x", padx=(4, 0))

        # 3. Results Table Header & Counter
        res_header_frame = ctk.CTkFrame(self, fg_color="transparent")
        res_header_frame.pack(fill="x", padx=20, pady=(5, 2))

        self.lbl_res_count = ctk.CTkLabel(res_header_frame, text="Showing 0 results", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_res_count.pack(side="left")

        # 4. Scrollable Table Box
        self.results_scroll = ctk.CTkScrollableFrame(self, corner_radius=8)
        self.results_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    def _execute_search(self):
        kw = self.entry_keyword.get().strip()
        dist = self.entry_district.get().strip()
        up = self.entry_upazila.get().strip()
        mz = self.entry_mouza.get().strip()
        own = self.entry_owner.get().strip()
        kh = self.entry_khatian.get().strip()
        dg = self.entry_dag.get().strip()

        results = self.on_search_cb(
            keyword=kw, district=dist, upazila=up, mouza=mz,
            owner=own, khatian=kh, dag=dg, limit=100
        )
        self.results_data = results
        self._display_results(results)

    def _display_results(self, results: List[Dict[str, Any]]):
        # Clear existing children
        for widget in self.results_scroll.winfo_children():
            widget.destroy()

        self.lbl_res_count.configure(text=f"Showing {len(results)} matching land records")

        if not results:
            lbl_empty = ctk.CTkLabel(self.results_scroll, text="No records match the specified search criteria.", font=ctk.CTkFont(size=12), text_color="gray60")
            lbl_empty.pack(pady=30)
            return

        # Render Table Header
        headers = ["Record ID", "District", "Upazila", "Mouza", "Khatian", "Dag", "Owner Name", "Land Type", "Area"]
        header_frame = ctk.CTkFrame(self.results_scroll, fg_color="#202020", corner_radius=4)
        header_frame.pack(fill="x", pady=(0, 4))
        header_frame.grid_columnconfigure(list(range(len(headers))), weight=1)

        for i, h in enumerate(headers):
            lbl = ctk.CTkLabel(header_frame, text=h, font=ctk.CTkFont(size=11, weight="bold"), text_color="white")
            lbl.grid(row=0, column=i, padx=4, pady=6, sticky="w")

        # Render Data Rows
        for idx, rec in enumerate(results):
            row_frame = ctk.CTkFrame(self.results_scroll, fg_color="#181818" if idx % 2 == 0 else "transparent", corner_radius=4)
            row_frame.pack(fill="x", pady=1)
            row_frame.grid_columnconfigure(list(range(len(headers))), weight=1)

            vals = [
                rec.get("record_id", ""), rec.get("district", ""), rec.get("upazila", ""),
                rec.get("mouza", ""), rec.get("khatian", ""), rec.get("dag", ""),
                rec.get("owner_name", ""), rec.get("land_type", ""), rec.get("area", "")
            ]

            for i, v in enumerate(vals):
                lbl = ctk.CTkLabel(row_frame, text=str(v), font=ctk.CTkFont(size=10))
                lbl.grid(row=0, column=i, padx=4, pady=4, sticky="w")
