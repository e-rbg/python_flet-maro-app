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
        
        # --- Cached Database Memory (Loaded ONCE in did_mount to prevent slow search lag) ---
        self.landowners = []
        self.municipalities = []
        self.all_barangays = []
        self.mother_titles = []

        # --- Reusable SnackBar ---
        self.snack_bar = ft.SnackBar(content=ft.Text(""))

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

        # --- Detail Window Dialog (The separate window popup) ---
        self.details_view = MotherTitleDetailsView()
        
        self.details_dialog = ft.AlertDialog(
            title=ft.Text("Property Structural Profile Tracking"),
            content=ft.Container(
                content=ft.Text("No record selected."), 
                width=950, 
                height=500
            ),
            actions=[
                ft.TextButton("Close View", on_click=self.close_details_dialog)
            ],
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

        # --- Build Initial Layout Content Matrix ---
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

    # 🚀 FIX: Lifecycle Mount Method to inject overlays safely into memory canvas
    def did_mount(self):
        if self.form_dialog not in self.page.overlay:
            self.page.overlay.append(self.form_dialog)
        if self.details_dialog not in self.page.overlay:
            self.page.overlay.append(self.details_dialog)
        if self.snack_bar not in self.page.overlay:
            self.page.overlay.append(self.snack_bar)
        
        # Hydrate memory cash values safely
        self.preload_database_cache()
        self.refresh_ui_components()

    def close_details_dialog(self, e):
        """Safely dismisses the view details modal popup."""
        self.details_dialog.open = False
        self.page.update()

    def handle_navigate_to_details(self, mt):
        if not mt:
            return

        # 1. Resolve geographic address text safely
        if mt.barangay and mt.barangay.municipality:
            prov_name = mt.barangay.municipality.province.name if mt.barangay.municipality.province else "Unknown Province"
            location_str = f"Brgy. {mt.barangay.name}, {mt.barangay.municipality.name}, {prov_name}"
        elif mt.barangay:
            location_str = f"Brgy. {mt.barangay.name} (Unlinked)"
        else:
            location_str = "Geographic Location Unrecorded"

        # 2. Build explicit content structure grid
        grid_content = ft.Row([
            # Left Panel: Core Registry Metadata Information Card
            ft.Container(
                expand=5,
                content=ft.Column([
                    ft.ListTile(
                        leading=ft.Icon(ft.icons.PERSON_PIN_ROUNDED, color=ft.colors.BLUE_700), 
                        title=ft.Text(f"{mt.landowner.name if mt.landowner else 'Unknown Landowner'}", size=15, weight=ft.FontWeight.W_500), 
                        subtitle=ft.Text("Registered Landowner")
                    ),
                    ft.ListTile(
                        leading=ft.Icon(ft.icons.LANDSCAPE_ROUNDED, color=ft.colors.GREEN_700), 
                        title=ft.Text(f"{mt.area_hectares} Hectares", size=15), 
                        subtitle=ft.Text("Area")
                    ),
                    ft.ListTile(
                        leading=ft.Icon(ft.icons.ASSIGNMENT_ROUNDED, color=ft.colors.ORANGE_700), 
                        title=ft.Text(f"{mt.mode_of_acquisition or '—'}", size=15), 
                        subtitle=ft.Text("Mode of Acquisition")
                    ),
                    ft.ListTile(
                        leading=ft.Icon(ft.icons.MAP_ROUNDED, color=ft.colors.PURPLE_700), 
                        title=ft.Text(f"{mt.lot_number or '—'} | Survey {mt.survey_number or '—'}", size=15), 
                        subtitle=ft.Text("Lot & Survey Details")
                    ),
                    ft.ListTile(
                        leading=ft.Icon(ft.icons.PIN_DROP_ROUNDED, color=ft.colors.RED_700), 
                        title=ft.Text(location_str, size=14, color=ft.colors.BLUE_GREY_700), 
                        subtitle=ft.Text("Location")
                    ),
                ], spacing=2, scroll=ft.ScrollMode.ADAPTIVE)
            ),
            
            # Separation line partition
            ft.VerticalDivider(width=1, color=ft.colors.GREY_300),
            
            # Right Panel: Large Descriptive Narrative Logs
            ft.Container(
                expand=6,
                padding=ft.padding.only(left=10),
                content=ft.Column([
                    ft.TextField(
                        label="Technical Metadata / Original Deed Narrative", 
                        value=mt.raw_text or "No narrative technical descriptions logged.",
                        multiline=True, 
                        read_only=True, 
                        min_lines=4, 
                        max_lines=5,
                    ),
                    ft.Container(height=5),
                    ft.TextField(
                        label="Boundary Coordinates / Line Traversal Mapping", 
                        value=mt.lines or "No boundary lines traversal mapped.",
                        multiline=True, 
                        read_only=True, 
                        min_lines=4, 
                        max_lines=5,
                    )
                ], alignment=ft.MainAxisAlignment.START, spacing=10)
            )
        ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START)

        # 3. Encapsulate into a scrollable structural master shell frame box
        dialog_body = ft.Container(
            content=grid_content,
            width=950,
            height=480,
            padding=10
        )

        # 4. Bind changes directly into your dialog layout references
        self.details_dialog.title = ft.Text(f"Title Number: {mt.title_number or 'Details'}", size=20, weight=ft.FontWeight.BOLD)
        self.details_dialog.content = dialog_body
        
        # 5. Open and commit updates to the screen active tree panel layout
        self.details_dialog.open = True
        self.page.update()

    # --- DATABASE PRELOADING ---
    def preload_database_cache(self):
        """Loads static variables safely to memory once so search rendering is instant."""
        self.landowners = get_all_landowners()
        self.municipalities = get_all_municipalities_global()
        self.all_barangays = get_all_barangays_global()
        self.mother_titles = get_all_mother_titles()

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
        """Filters the table instantly without refreshing data from disk."""
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
        # Update Dropdown options safely with preloaded cache data
        self.landowner_dropdown.options = [ft.dropdown.Option(key=str(l.id), text=l.name) for l in self.landowners]
        self.mun_dropdown.options = [
            ft.dropdown.Option(
                key=str(m.id), 
                text=f"{m.name} ({m.province.name})" if m.province else f"{m.name} (Unknown)"
            ) for m in self.municipalities
        ]

        # Read search input criteria
        query = self.search_input.value.strip().lower()

        # Rebuild layout data rows
        self.titles_table.rows.clear()
        for mt in self.mother_titles:
            title_num = mt.title_number.lower() if mt.title_number else ""
            owner_name = mt.landowner.name.lower() if mt.landowner else "unknown"

            # Search Filter Trap Rule
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
                                on_click=lambda e, title_item=mt: self.handle_navigate_to_details(title_item)
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
        
        self.preload_database_cache()
        self.refresh_ui_components()

    def handle_delete(self, title_id):
        delete_mother_title(title_id)
        self.show_snack("Title registration data entry purged.")
        self.preload_database_cache()
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
        self.snack_bar.content.value = message
        self.snack_bar.open = True
        self.page.update()