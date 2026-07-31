"""
Downloaded File Selection Manager Tab for DLRS Data Extractor Pro v2.0
Interactive file list with checkboxes for selecting files before triggering Stage 2 Conversion.
"""

import os
import customtkinter as ctk
from typing import Callable, List, Dict, Any

class FileManagerTab(ctk.CTkFrame):
    """Stage 1.5 File Selector & Manager View."""

    def __init__(self, master, on_start_conversion: Callable[[List[str]], None], output_root_dir: str = "./Output"):
        super().__init__(master, corner_radius=10)
        self.on_start_conversion_cb = on_start_conversion
        self.output_root_dir = os.path.abspath(output_root_dir)
        self.file_items: List[Dict[str, Any]] = []

        self._build_ui()
        self.refresh_file_list()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        # 1. Header & Controls Panel
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 5))

        lbl_title = ctk.CTkLabel(
            header_frame,
            text="Downloaded Files Manager (Stage 1 Output)",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold")
        )
        lbl_title.pack(side="left")

        # Action Toolbar
        toolbar_frame = ctk.CTkFrame(self, corner_radius=8)
        toolbar_frame.pack(fill="x", padx=20, pady=8)

        btn_select_all = ctk.CTkButton(toolbar_frame, text="✓ Select All", width=95, command=self._select_all)
        btn_select_all.pack(side="left", padx=8, pady=8)

        btn_deselect_all = ctk.CTkButton(toolbar_frame, text="✗ Deselect All", width=105, fg_color="gray40", command=self._deselect_all)
        btn_deselect_all.pack(side="left", padx=4, pady=8)

        btn_refresh = ctk.CTkButton(toolbar_frame, text="🔄 Refresh", width=90, fg_color="#1568B2", command=self.refresh_file_list)
        btn_refresh.pack(side="left", padx=4, pady=8)

        self.lbl_selected_counter = ctk.CTkLabel(toolbar_frame, text="Selected: 0 files", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_selected_counter.pack(side="left", padx=15)

        # Convert Action Button
        btn_convert = ctk.CTkButton(
            toolbar_frame,
            text="⚡ Convert & Extract Selected Files (Stage 2) ▶",
            fg_color="#00A63E", hover_color="#008532",
            font=ctk.CTkFont(size=13, weight="bold"), height=36,
            command=self._handle_convert_click
        )
        btn_convert.pack(side="right", padx=10, pady=8)

        # 2. Scrollable File Table List
        self.table_scroll = ctk.CTkScrollableFrame(self, corner_radius=8)
        self.table_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    def refresh_file_list(self):
        """Scan Output directories for downloaded files."""
        self.file_items.clear()
        search_dirs = [
            os.path.join(self.output_root_dir, "PDFs"),
            os.path.join(self.output_root_dir, "HTML"),
            os.path.join(self.output_root_dir, "Images"),
            os.path.join(self.output_root_dir, "Documents")
        ]

        for s_dir in search_dirs:
            if os.path.exists(s_dir):
                for root, _, files in os.walk(s_dir):
                    for f in files:
                        if f.endswith(".gitkeep"):
                            continue
                        f_path = os.path.join(root, f)
                        rel_dist = os.path.basename(root) if root != s_dir else "General"
                        size_mb = os.path.getsize(f_path) / (1024 * 1024)
                        ext = os.path.splitext(f)[1].lower()

                        self.file_items.append({
                            "path": f_path,
                            "filename": f,
                            "district": rel_dist,
                            "size_mb": size_mb,
                            "ext": ext,
                            "var": ctk.BooleanVar(value=True)
                        })

        self._render_table()

    def _render_table(self):
        for w in self.table_scroll.winfo_children():
            w.destroy()

        if not self.file_items:
            lbl_empty = ctk.CTkLabel(
                self.table_scroll,
                text="No downloaded files found in Output/. Run Stage 1 Download first.",
                font=ctk.CTkFont(size=12), text_color="gray60"
            )
            lbl_empty.pack(pady=40)
            self._update_counter()
            return

        # Table Header
        header = ctk.CTkFrame(self.table_scroll, fg_color="#202020", corner_radius=4)
        header.pack(fill="x", pady=(0, 4))
        header.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        ctk.CTkLabel(header, text="Select", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=0, padx=8, pady=6, sticky="w")
        ctk.CTkLabel(header, text="Format", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=1, padx=8, pady=6, sticky="w")
        ctk.CTkLabel(header, text="Filename", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=2, padx=8, pady=6, sticky="w")
        ctk.CTkLabel(header, text="District", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=3, padx=8, pady=6, sticky="w")
        ctk.CTkLabel(header, text="Size", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=4, padx=8, pady=6, sticky="w")

        # Table Data Rows
        for idx, item in enumerate(self.file_items):
            row = ctk.CTkFrame(self.table_scroll, fg_color="#181818" if idx % 2 == 0 else "transparent", corner_radius=4)
            row.pack(fill="x", pady=1)
            row.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

            chk = ctk.CTkCheckBox(row, text="", variable=item["var"], width=20, command=self._update_counter)
            chk.grid(row=0, column=0, padx=8, pady=4, sticky="w")

            lbl_ext = ctk.CTkLabel(row, text=item["ext"].upper(), font=ctk.CTkFont(size=10, weight="bold"), text_color="#00A63E")
            lbl_ext.grid(row=0, column=1, padx=8, pady=4, sticky="w")

            lbl_fn = ctk.CTkLabel(row, text=item["filename"], font=ctk.CTkFont(size=11))
            lbl_fn.grid(row=0, column=2, padx=8, pady=4, sticky="w")

            lbl_dist = ctk.CTkLabel(row, text=item["district"], font=ctk.CTkFont(size=11))
            lbl_dist.grid(row=0, column=3, padx=8, pady=4, sticky="w")

            lbl_sz = ctk.CTkLabel(row, text=f"{item['size_mb']:.2f} MB", font=ctk.CTkFont(size=10))
            lbl_sz.grid(row=0, column=4, padx=8, pady=4, sticky="w")

        self._update_counter()

    def _select_all(self):
        for item in self.file_items:
            item["var"].set(True)
        self._update_counter()

    def _deselect_all(self):
        for item in self.file_items:
            item["var"].set(False)
        self._update_counter()

    def _update_counter(self):
        selected_count = sum(1 for item in self.file_items if item["var"].get())
        self.lbl_selected_counter.configure(text=f"Selected: {selected_count}/{len(self.file_items)} files")

    def _handle_convert_click(self):
        selected_paths = [item["path"] for item in self.file_items if item["var"].get()]
        if selected_paths:
            self.on_start_conversion_cb(selected_paths)
