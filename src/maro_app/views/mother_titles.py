import flet as ft
from src.maro_app.database import (
    get_all_mother_titles, get_all_landowners, 
    get_all_municipalities_global, get_all_barangays_global,
    save_mother_title, delete_mother_title
)
from src.maro_app.views.mother_title_details import MotherTitleDetailsView

class MotherTitlesView(ft.Container):
    def __init__(self, on_view_change=None):
        super().__init__(padding=20, alignment=ft.alignment.top_left)
        self.on_view_change = on_view_change 
        self.editing_title_id = None
        
        # --- Search Bar Control ---
        self.search_input = ft.TextField(
            label="Search Mother Titles...",
            hint_text="Type Title No. or Landowner Name to filter...",
            prefix_icon=ft.icons.SEARCH,
            expand=True,
            on_change=self.handle_search_changed
        )

        # --- Form Controls (Housed in Dialog) ---
        self.title_input = ft.TextField(label="OCT/TCT Number", expand=True)
        self.landowner_dropdown = ft.Dropdown(label="Registered Landowner", expand=True)
        self.area_input = ft.TextField(label="Total Area (Hectares)", expand=True)
        self.lot_input = ft.TextField(label="Lot Number", expand=True)
        self.survey_input = ft.TextField(label="Survey Number", expand=True)
        
        self.mode_dropdown = ft.Dropdown(
            label="Mode of Acquisition",
            expand=True,
            options=[
                ft.dropdown.Option("OLT"),
                ft.dropdown.Option("GFI"),
                ft.dropdown.Option("VOS"),
                ft.dropdown.Option("CA"),
            ]
        )

        self.mun_dropdown = ft.Dropdown(
            label="Municipality (Province)", 
            expand=True, 
            on_change=self.handle_municipality_changed
        )
        self.bar_dropdown = ft.Dropdown(label="Barangay", expand=True, disabled=True)

        self.raw_text_input = ft.TextField(label="Raw Deed Text / Technical Metadata", multiline=True, min_lines=2, max_lines=4, expand=True)
        self.lines_input = ft.TextField(label="Boundary Coordinates / Line Traversal", multiline=True, min_lines=2, max_lines=4, expand=True)

        # --- Modal Form Action Buttons ---
        self.cancel_btn = ft.TextButton("Cancel", on_click=self.close_form_dialog)
        self.submit_btn = ft.ElevatedButton(
            "Save Record", 
            bgcolor=ft.colors.BLUE_700, 
            color=ft.colors.WHITE, 
            on_click=self.handle_submit_form
        )

        # --- The Operational Dialog Modal Window ---
        self.form_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Register Mother Title Data", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                width=650,
                height=520,
                content=ft.Column([
                    ft.Row([self.title_input, self.landowner_dropdown]),
                    ft.Row([self.area_input, self.mode_dropdown]),
                    ft.Row([self.lot_input, self.survey_input]),
                    ft.Row([self.mun_dropdown, self.bar_dropdown]),
                    ft.Row([self.raw_text_input]),
                    ft.Row([self.lines_input]),
                ], spacing=12, scroll=ft.ScrollMode.ALWAYS)
            ),
            actions=[self.cancel_btn, self.submit_btn],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        # --- Detail Window Dialog ---
        self.details_view = MotherTitleDetailsView()
        self.details_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Mother Title Hierarchy Explorer", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                width=1100,
                height=720,
                content=self.details_view,
                padding=0,
            ),
            actions=[ft.TextButton("Close", on_click=self.close_details_dialog)],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        # --- Master Grid Data Table ---
        self.titles_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Title No.", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Landowner", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Area (Ha)", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Location Hierarchy", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Acquisition", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Actions", weight=ft.FontWeight.BOLD)),
            ],
            rows=[]
        )

    def handle_navigate_to_details(self, mt):
        if not mt:
            return

        self.details_dialog.title.value = f"Mother Title Hierarchy: {mt.title_number or 'Details'}"
        self.details_view.preload_titles_dropdown()
        self.details_view.load_specific_title(mt.id)
        self.details_dialog.open = True
        self.page.update()

    def close_details_dialog(self, e=None):
        self.details_dialog.open = False
        self.page.update()

    def did_mount(self):
        if self.form_dialog not in self.page.overlay:
            self.page.overlay.append(self.form_dialog)
        if self.details_dialog not in self.page.overlay:
            self.page.overlay.append(self.details_dialog)
        
        params = self.page.route.split("?id=")[-1] if "?id=" in self.page.route else None
        if params and params.isdigit():
            self.title_selector.value = params
            self.handle_title_selected(None) # Trigger auto-load

        header_actions = ft.Row([
            ft.Column([
                ft.Text("Mother Titles Repository", size=26, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_GREY_800),
                ft.Text("Master records index of properties prior to individual parcel splits.", size=14, color=ft.colors.GREY_600),
            ]),
            ft.ElevatedButton(
                "Add Mother Title",
                icon=ft.icons.ADD,
                bgcolor=ft.colors.BLUE_700,
                color=ft.colors.WHITE,
                on_click=self.open_add_dialog
            )
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        # Inject the search bar row right beneath the header actions layout section
        self.content = ft.Column([
            header_actions,
            ft.Divider(height=15, color=ft.colors.TRANSPARENT),
            ft.Row([self.search_input]),
            ft.Divider(height=15),
            ft.Row([self.titles_table], scroll=ft.ScrollMode.ALWAYS)
        ], 
        alignment=ft.MainAxisAlignment.START,
        scroll=ft.ScrollMode.ALWAYS
        )

        self.refresh_ui_components()

    # --- DIALOG LIFECYCLE MANAGEMENT ---

    def open_add_dialog(self, e):
        self.clear_form_fields()
        self.form_dialog.title.value = "Register New Mother Title Data"
        self.submit_btn.text = "Save Record"
        self.submit_btn.bgcolor = ft.colors.BLUE_700
        self.form_dialog.open = True
        self.page.update()

    def close_form_dialog(self, e=None):
        self.form_dialog.open = False
        self.page.update()

    # --- SEARCH & FILTER HANDLER ---

    def handle_search_changed(self, e):
        """Triggers a table recalculation layout whenever the text changes."""
        self.refresh_ui_components()

    # --- DROPDOWN CASCADE LOGIC ---

    def handle_municipality_changed(self, e):
        if not self.mun_dropdown.value:
            self.bar_dropdown.disabled = True
            self.bar_dropdown.value = None
            self.page.update()
            return

        selected_mun_id = int(self.mun_dropdown.value)
        filtered_barangays = [b for b in self.all_barangays if b.municipality_id == selected_mun_id]
        
        self.bar_dropdown.options = [ft.dropdown.Option(key=str(b.id), text=b.name) for b in filtered_barangays]
        self.bar_dropdown.disabled = False
        self.bar_dropdown.value = None
        self.page.update()

    # --- REFRESH CORE WITH SEARCH FILTERING ---

    def refresh_ui_components(self):
        landowners = get_all_landowners()
        self.municipalities = get_all_municipalities_global()
        self.all_barangays = get_all_barangays_global()
        mother_titles = get_all_mother_titles()

        # Update Form Dropdowns
        self.landowner_dropdown.options = [ft.dropdown.Option(key=str(l.id), text=l.name) for l in landowners]
        self.mun_dropdown.options = [
            ft.dropdown.Option(
                key=str(m.id), 
                text=f"{m.name} ({m.province.name})" if m.province else f"{m.name} (Unknown)"
            ) for m in self.municipalities
        ]

        # Read current search text query
        query = self.search_input.value.strip().lower()

        # Rebuild Filtered Grid Table
        self.titles_table.rows.clear()
        for mt in mother_titles:
            title_num = mt.title_number.lower() if mt.title_number else ""
            owner_name = mt.landowner.name.lower() if mt.landowner else "unknown"

            # Skip displaying this item if a search filter query exists and doesn't match
            if query and (query not in title_num and query not in owner_name):
                continue

            if mt.barangay and mt.barangay.municipality:
                p_name = mt.barangay.municipality.province.name if mt.barangay.municipality.province else "Unknown"
                location_text = f"{mt.barangay.name}, {mt.barangay.municipality.name}, {p_name}"
            elif mt.barangay:
                location_text = f"{mt.barangay.name} (Unlinked)"
            else:
                location_text = "—"

            self.titles_table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(mt.title_number, weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text(mt.landowner.name if mt.landowner else "Unknown")),
                    ft.DataCell(ft.Text(str(mt.area_hectares))),
                    ft.DataCell(ft.Text(location_text, size=13)),
                    ft.DataCell(ft.Text(mt.mode_of_acquisition or "—")),
                    ft.DataCell(
                        ft.Row([
                            ft.IconButton(
                                ft.icons.VISIBILITY_ROUNDED, 
                                icon_color=ft.colors.GREEN_700, 
                                tooltip="View Detailed Hierarchy",
                                on_click=lambda e, mt=mt: self.handle_navigate_to_details(mt)
                            ),
                            ft.IconButton(ft.icons.EDIT_ROUNDED, icon_color=ft.colors.BLUE_600, on_click=lambda e, title=mt: self.handle_load_edit(title)),
                            ft.IconButton(ft.icons.DELETE_OUTLINE_ROUNDED, icon_color=ft.colors.RED_400, on_click=lambda e, id=mt.id: self.handle_delete(id)),
                        ])
                    )
                ])
            )
        self.update()

    # --- TRANSACTION HANDLERS ---

    def handle_load_edit(self, mt):
        self.editing_title_id = mt.id
        self.title_input.value = mt.title_number
        self.landowner_dropdown.value = str(mt.landowner_id) if mt.landowner_id else None
        self.area_input.value = str(mt.area_hectares)
        self.lot_input.value = mt.lot_number or ""
        self.survey_input.value = mt.survey_number or ""
        self.mode_dropdown.value = mt.mode_of_acquisition or None
        self.raw_text_input.value = mt.raw_text or ""
        self.lines_input.value = mt.lines or ""

        if mt.barangay:
            self.mun_dropdown.value = str(mt.barangay.municipality_id)
            filtered_barangays = [b for b in self.all_barangays if b.municipality_id == mt.barangay.municipality_id]
            self.bar_dropdown.options = [ft.dropdown.Option(key=str(b.id), text=b.name) for b in filtered_barangays]
            self.bar_dropdown.disabled = False
            self.bar_dropdown.value = str(mt.barangay_id)
        else:
            self.mun_dropdown.value = None
            self.bar_dropdown.value = None
            self.bar_dropdown.disabled = True

        self.form_dialog.title.value = f"Modify Title Details: {mt.title_number}"
        self.submit_btn.text = "Update Entry"
        self.submit_btn.bgcolor = ft.colors.ORANGE_700
        
        self.form_dialog.open = True
        self.page.update()

    def handle_submit_form(self, e):
        title_num = self.title_input.value.strip()
        landowner_id = self.landowner_dropdown.value
        area_val = self.area_input.value.strip()
        barangay_id = self.bar_dropdown.value

        if not title_num or not landowner_id or not area_val or not barangay_id:
            self.show_snack("Validation Error: Missing mandatory form details!")
            return

        try:
            parsed_area = float(area_val)
        except ValueError:
            self.show_snack("Validation Error: Total area volume must be a raw float value number.")
            return

        save_mother_title(
            title_number=title_num,
            landowner_id=int(landowner_id),
            area=parsed_area,
            lot_number=self.lot_input.value.strip(),
            survey_number=self.survey_input.value.strip(),
            mode_of_acquisition=self.mode_dropdown.value,
            raw_text=self.raw_text_input.value.strip(),
            lines=self.lines_input.value.strip(),
            barangay_id=int(barangay_id),
            title_id=self.editing_title_id
        )

        self.close_form_dialog()
        self.show_snack("Mother Title records successfully updated.")
        self.clear_form_fields()
        self.refresh_ui_components()

    def handle_delete(self, title_id):
        delete_mother_title(title_id)
        self.show_snack("Title registration data entry purged.")
        self.refresh_ui_components()

    def clear_form_fields(self):
        self.editing_title_id = None
        self.title_input.value = ""
        self.landowner_dropdown.value = None
        self.area_input.value = ""
        self.lot_input.value = ""
        self.survey_input.value = ""
        self.mode_dropdown.value = None
        self.mun_dropdown.value = None
        self.bar_dropdown.value = None
        self.bar_dropdown.disabled = True
        self.raw_text_input.value = ""
        self.lines_input.value = ""

    def show_snack(self, message):
        self.page.overlay.append(ft.SnackBar(ft.Text(message), open=True))
        self.page.update()