import flet as ft
from src.maro_app.database import (
    get_all_individual_titles, get_all_mother_titles,
    save_individual_title, delete_individual_title
)
import uuid

class IndividualTitlesView(ft.Container):
    def __init__(self, on_view_change=None):
        super().__init__(padding=20, alignment=ft.alignment.top_left)
        self.on_view_change = on_view_change 
        self.editing_title_id = None
        
        # --- Memory Cache Pools ---
        self.individual_titles = []
        self.mother_titles = []

        self.snack_bar = ft.SnackBar(content=ft.Text(""))

        self.search_input = ft.TextField(
            label="Search Individual Titles...",
            hint_text="Filter by Title No. or Parent Title No...",
            prefix_icon=ft.icons.SEARCH,
            expand=True,
            on_change=self.handle_search_changed
        )

        # --- Dynamic Form Fields ---
        self.title_input = ft.TextField(label="Individual Title Number (title_number)", expand=True)
        self.mother_title_dropdown = ft.Dropdown(label="Parent Mother Title Link", expand=True)
        self.survey_input = ft.TextField(label="Survey Number", expand=True)
        
        self.cloa_type_dropdown = ft.Dropdown(
            label="CLOA Allocation Type",
            expand=True,
            value="Individual",
            options=[
                ft.dropdown.Option("Individual"),
                ft.dropdown.Option("Collective")
            ]
        )
        self.area_input = ft.TextField(label="Area Scale (Hectares)", expand=True)
        
        # Date slots (Parsed gracefully by backend helper utilities)
        self.reg_date_input = ft.TextField(label="Date Registered (YYYY-MM-DD)", hint_text="e.g., 2026-06-03", expand=True)
        self.dist_date_input = ft.TextField(label="Date Distributed (YYYY-MM-DD)", hint_text="e.g., 2026-06-15", expand=True)
        
        self.status_dropdown = ft.Dropdown(
            label="Operational Status",
            expand=True,
            value="active",
            options=[
                ft.dropdown.Option("active"),
                ft.dropdown.Option("cancelled"),
                ft.dropdown.Option("pending")
            ]
        )

        self.raw_text_input = ft.TextField(label="Technical Descriptions Metadata (raw_text)", multiline=True, min_lines=2, max_lines=4, expand=True)
        self.lines_input = ft.TextField(label="Boundary Line JSON String (lines)", multiline=True, min_lines=2, max_lines=4, expand=True)

        self.cancel_btn = ft.TextButton("Cancel", on_click=self.close_form_dialog)
        self.submit_btn = ft.ElevatedButton("Save Record", bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE, on_click=self.handle_submit_form)

        # --- Modal Form Control System ---
        self.form_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Register Individual Title Record", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                width=650,
                height=520,
                content=ft.Column([
                    ft.Row([self.title_input, self.mother_title_dropdown]),
                    ft.Row([self.survey_input, self.cloa_type_dropdown]),
                    ft.Row([self.area_input, self.status_dropdown]),
                    ft.Row([self.reg_date_input, self.dist_date_input]),
                    ft.Row([self.raw_text_input]),
                    ft.Row([self.lines_input]),
                ], spacing=12, scroll=ft.ScrollMode.ALWAYS)
            ),
            actions=[self.cancel_btn, self.submit_btn],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        # --- View Details Window Framework ---
        self.details_dialog = ft.AlertDialog(
            title=ft.Text("Individual Split Structural Profile"),
            content=ft.Container(content=ft.Text("No record selected."), width=900, height=420),
            actions=[ft.TextButton("Close View", on_click=self.close_details_dialog)],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.titles_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Individual Title", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Parent Title", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("CLOA Type", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Area (Ha)", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Status", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Actions", weight=ft.FontWeight.BOLD)),
            ],
            rows=[]
        )

        header_actions = ft.Row([
            ft.Column([
                ft.Text("Individual Titles Repository", size=26, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_GREY_800),
                ft.Text("Tracking individual and collective land parcel splits derived from Mother Titles.", size=14, color=ft.colors.GREY_600),
            ]),
            ft.ElevatedButton("Add Individual Title", icon=ft.icons.ADD, bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE, on_click=self.open_add_dialog)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        self.content = ft.Column([
            header_actions,
            ft.Divider(height=15, color=ft.colors.TRANSPARENT),
            ft.Row([self.search_input]),
            ft.Divider(height=15),
            ft.Row([self.titles_table], scroll=ft.ScrollMode.ALWAYS)
        ], alignment=ft.MainAxisAlignment.START, scroll=ft.ScrollMode.ALWAYS)

    def did_mount(self):
        # Prevent Flet crashes by validating registry state context layers first
        if self.form_dialog not in self.page.overlay:
            self.page.overlay.append(self.form_dialog)
        if self.details_dialog not in self.page.overlay:
            self.page.overlay.append(self.details_dialog)
        if self.snack_bar not in self.page.overlay:
            self.page.overlay.append(self.snack_bar)
        
        self.preload_database_cache()
        self.refresh_ui_components()

    def preload_database_cache(self):
        self.individual_titles = get_all_individual_titles()
        self.mother_titles = get_all_mother_titles()

    def close_details_dialog(self, e):
        self.details_dialog.open = False
        self.page.update()

    def handle_navigate_to_details(self, it):
        if not it:
            return

        grid_content = ft.Row([
            ft.Container(
                expand=5,
                content=ft.Column([
                    ft.ListTile(leading=ft.Icon(ft.icons.ACCOUNT_BALANCE_WALLET, color=ft.colors.BLUE_900), title=ft.Text(f"OCT/TCT No: {it.title_number}", size=15, weight=ft.FontWeight.BOLD), subtitle=ft.Text("Individual Split Profile Reference")),
                    ft.ListTile(leading=ft.Icon(ft.icons.LAYERS, color=ft.colors.BLUE_700), title=ft.Text(f"Parent Record: {it.mother_title.title_number if it.mother_title else 'Independent'}", size=15), subtitle=ft.Text("Ancestor Mother Title Lineage")),
                    ft.ListTile(leading=ft.Icon(ft.icons.ASSIGNMENT_IND, color=ft.colors.GREEN_700), title=ft.Text(f"CLOA Classification: {it.cloa_type}", size=15), subtitle=ft.Text("Land Reform Tenure Distribution Mode")),
                    ft.ListTile(leading=ft.Icon(ft.icons.LANDSCAPE, color=ft.colors.ORANGE_700), title=ft.Text(f"Total Scaled Footprint: {it.area} Hectares", size=15), subtitle=ft.Text("Spatial Area Computations")),
                    ft.ListTile(leading=ft.Icon(ft.icons.GRID_ON, color=ft.colors.PURPLE_700), title=ft.Text(f"Survey Number: {it.survey_number or '—'}", size=15), subtitle=ft.Text("Cadastral Identity Blueprint Specs")),
                ], spacing=2, scroll=ft.ScrollMode.ADAPTIVE)
            ),
            ft.VerticalDivider(width=1, color=ft.colors.GREY_300),
            ft.Container(
                expand=5,
                padding=ft.padding.only(left=10),
                content=ft.Column([
                    ft.ListTile(leading=ft.Icon(ft.icons.CALENDAR_TODAY, color=ft.colors.TEAL), title=ft.Text(f"Registered: {it.date_registered or 'Pending Logging'}", size=14), subtitle=ft.Text("Registry Operational Entry Timestamp")),
                    ft.ListTile(leading=ft.Icon(ft.icons.LOCAL_SHIPPING, color=ft.colors.INDIGO), title=ft.Text(f"Distributed: {it.date_distributed or 'Pending Handover'}", size=14), subtitle=ft.Text("Physical Tenancy Handover Mandate")),
                    ft.Divider(height=10),
                    ft.TextField(label="Technical Descriptions Text", value=it.raw_text or "No deed tracking notes compiled.", multiline=True, read_only=True, min_lines=3, max_lines=4),
                ], alignment=ft.MainAxisAlignment.START)
            )
        ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START)

        self.details_dialog.title = ft.Text(f"Individual Data Sheet: {it.title_number}", size=20, weight=ft.FontWeight.BOLD)
        self.details_dialog.content = ft.Container(content=grid_content, width=900, height=400, padding=10)
        self.details_dialog.open = True
        self.page.update()

    def handle_search_changed(self, e):
        self.refresh_ui_components()

    def refresh_ui_components(self):
        self.mother_title_dropdown.options = [ft.dropdown.Option(key=str(m.id), text=f"OCT/TCT: {m.title_number}") for m in self.mother_titles]

        query = self.search_input.value.strip().lower()
        self.titles_table.rows.clear()

        for it in self.individual_titles:
            t_num = it.title_number.lower() if it.title_number else ""
            parent = it.mother_title.title_number.lower() if it.mother_title else "independent"

            if query and (query not in t_num and query not in parent):
                continue

            self.titles_table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(it.title_number, weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text(it.mother_title.title_number if it.mother_title else "Independent")),
                    ft.DataCell(ft.Text(it.cloa_type)),
                    ft.DataCell(ft.Text(str(it.area))),
                    ft.DataCell(ft.Text(it.status.upper(), color=ft.colors.GREEN_700 if it.status == 'active' else ft.colors.RED_400)),
                    ft.DataCell(
                        ft.Row([
                            ft.IconButton(ft.icons.VISIBILITY_ROUNDED, icon_color=ft.colors.GREEN_700, on_click=lambda e, item=it: self.handle_navigate_to_details(item)),
                            ft.IconButton(ft.icons.EDIT_ROUNDED, icon_color=ft.colors.BLUE_600, on_click=lambda e, item=it: self.handle_load_edit(item)),
                            ft.IconButton(ft.icons.DELETE_OUTLINE_ROUNDED, icon_color=ft.colors.RED_400, on_click=lambda e, fid=it.id: self.handle_delete(fid)),
                        ])
                    )
                ])
            )
        self.update()

    def open_add_dialog(self, e):
        self.clear_form_fields()
        self.form_dialog.title.value = "Register Individual Title Record"
        self.submit_btn.text = "Save Record"
        self.submit_btn.bgcolor = ft.colors.BLUE_700
        self.form_dialog.open = True
        self.page.update()

    def close_form_dialog(self, e=None):
        self.form_dialog.open = False
        self.page.update()

    def handle_load_edit(self, it):
        self.editing_title_id = it.id
        self.title_input.value = it.title_number
        self.mother_title_dropdown.value = str(it.mother_title_id) if it.mother_title_id else None
        self.survey_input.value = it.survey_number or ""
        self.cloa_type_dropdown.value = it.cloa_type
        self.area_input.value = str(it.area)
        self.reg_date_input.value = str(it.date_registered) if it.date_registered else ""
        self.dist_date_input.value = str(it.date_distributed) if it.date_distributed else ""
        self.raw_text_input.value = it.raw_text or ""
        self.lines_input.value = it.lines or ""
        self.status_dropdown.value = it.status

        self.form_dialog.title.value = f"Modify Individual Entry: {it.title_number}"
        self.submit_btn.text = "Update Entry"
        self.submit_btn.bgcolor = ft.colors.ORANGE_700
        self.form_dialog.open = True
        self.page.update()

    def handle_submit_form(self, e):
        t_no = self.title_input.value.strip()
        m_id = self.mother_title_dropdown.value
        a_val = self.area_input.value.strip()

        if not t_no or not m_id or not a_val:
            self.show_snack("Validation Error: Missing mandatory entries (title_number, parent link, and area size).")
            return

        try:
            parsed_area = float(a_val)
        except ValueError:
            self.show_snack("Validation Error: Area size scale metrics must be a floating numeric.")
            return

        reg_dt = self.reg_date_input.value.strip() or None
        dist_dt = self.dist_date_input.value.strip() or None

        # Call the unified, refactored backend logic cleanly
        save_individual_title(
            title_number=t_no,
            mother_title_id=m_id,
            cloa_type=self.cloa_type_dropdown.value,
            area=parsed_area,
            survey_number=self.survey_input.value.strip() or None,
            date_registered=reg_dt,
            date_distributed=dist_dt,
            raw_text=self.raw_text_input.value.strip() or None,
            lines=self.lines_input.value.strip() or None,
            status=self.status_dropdown.value,
            title_id=self.editing_title_id
        )

        self.close_form_dialog()
        self.show_snack("Individual ledger profile entries logged successfully.")
        self.clear_form_fields()
        self.preload_database_cache()
        self.refresh_ui_components()

    def handle_delete(self, title_id):
        delete_individual_title(title_id)
        self.show_snack("Individual title record tracking marker dropped.")
        self.preload_database_cache()
        self.refresh_ui_components()

    def clear_form_fields(self):
        self.editing_title_id = None
        self.title_input.value = ""
        self.mother_title_dropdown.value = None
        self.survey_input.value = ""
        self.cloa_type_dropdown.value = "Individual"
        self.area_input.value = ""
        self.reg_date_input.value = ""
        self.dist_date_input.value = ""
        self.status_dropdown.value = "active"
        self.raw_text_input.value = ""
        self.lines_input.value = ""

    def show_snack(self, message):
        self.snack_bar.content.value = message
        self.snack_bar.open = True
        self.page.update()