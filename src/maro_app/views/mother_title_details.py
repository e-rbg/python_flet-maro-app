import flet as ft
from src.maro_app.database import get_all_mother_titles

class MotherTitleDetailsView(ft.Container):
    def __init__(self):
        super().__init__(
            padding=20,
            alignment=ft.alignment.top_left
        )
        
        # --- Top Selection Control ---
        self.title_selector = ft.Dropdown(
            label="Select Mother OCT/TCT Title Number to Audit",
            expand=True,
            on_change=self.handle_title_selected
        )

        # --- Dynamic Core Summary Metadata Cards ---
        self.landowner_text = ft.Text("—", size=16, weight=ft.FontWeight.W_500, color=ft.colors.BLUE_GREY_900)
        self.area_text = ft.Text("—", size=16, weight=ft.FontWeight.W_500, color=ft.colors.BLUE_GREY_900)
        self.location_text = ft.Text("—", size=16, weight=ft.FontWeight.W_500, color=ft.colors.BLUE_GREY_900)
        self.acquisition_text = ft.Text("—", size=16, weight=ft.FontWeight.W_500, color=ft.colors.BLUE_GREY_900)
        self.survey_lot_text = ft.Text("—", size=16, weight=ft.FontWeight.W_500, color=ft.colors.BLUE_GREY_900)

        # --- Table 1: Individual Titles Split Grid ---
        self.individual_titles_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Individual Title No.", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Allocated Area (Ha)", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("CLOA / Patent No.", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Status", weight=ft.FontWeight.BOLD)),
            ],
            rows=[]
        )

        # --- Table 2: Assigned Agrarian Reform Beneficiaries (ARBs) ---
        self.beneficiaries_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ARB Name", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Assigned Title", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Area Share (Ha)", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Contact / Remarks", weight=ft.FontWeight.BOLD)),
            ],
            rows=[]
        )

        # Container wrapper for when data is ready to be painted
        self.details_layout = ft.Column(visible=False, spacing=20)

    def did_mount(self):
        # Header text layout block
        header = ft.Column([
            ft.Text("Mother Title Hierarchy Explorer", size=26, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_GREY_800),
            ft.Text("Trace land parcelization lineage down to individual titles and target ARB distributions.", size=14, color=ft.colors.GREY_600),
        ])

        # Summary Info Metadata Card Design
        summary_card = ft.Card(
            content=ft.Container(
                padding=20,
                content=ft.Column([
                    ft.Text("Primary Property Profile", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700),
                    ft.Divider(height=10, color=ft.colors.BLUE_200),
                    ft.Row([
                        ft.Column([ft.Text("Registered Landowner:", size=12, color=ft.colors.GREY_600), self.landowner_text], expand=True),
                        ft.Column([ft.Text("Total Base Area:", size=12, color=ft.colors.GREY_600), self.area_text], expand=True),
                    ]),
                    ft.Row([
                        ft.Column([ft.Text("Geographic Location:", size=12, color=ft.colors.GREY_600), self.location_text], expand=True),
                        ft.Column([ft.Text("Acquisition Mode / Survey Details:", size=12, color=ft.colors.GREY_600), self.survey_lot_text], expand=True),
                    ]),
                ], spacing=12)
            ),
            elevation=2
        )

        # Assemble the placeholder target grid columns layout
        self.details_layout.controls = [
            summary_card,
            ft.Text("Generated Individual Sub-Titles Inventory", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_GREY_700),
            ft.Row([self.individual_titles_table], scroll=ft.ScrollMode.ALWAYS),
            ft.Divider(height=10, color=ft.colors.TRANSPARENT),
            ft.Text("Distributed Agrarian Reform Beneficiaries (ARBs)", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_GREY_700),
            ft.Row([self.beneficiaries_table], scroll=ft.ScrollMode.ALWAYS),
        ]

        # Combine whole view canvas frame layout string
        self.content = ft.Column([
            header,
            ft.Divider(height=15),
            ft.Row([self.title_selector]),
            ft.Divider(height=15, color=ft.colors.TRANSPARENT),
            self.details_layout
        ], 
        alignment=ft.MainAxisAlignment.START,
        scroll=ft.ScrollMode.ALWAYS
        )

        self.preload_titles_dropdown()
    
    def load_specific_title(self, title_id):
        self.title_selector.value = str(title_id)
        # Call the existing selection logic
        self.handle_title_selected(None) 
        self.update()

    def preload_titles_dropdown(self):
        """Fetches mother titles from backend and updates choice lists."""
        self.mother_titles_list = get_all_mother_titles()
        self.title_selector.options = [
            ft.dropdown.Option(key=str(mt.id), text=f"OCT/TCT No. {mt.title_number} — {mt.landowner.name if mt.landowner else 'Unknown'}")
            for mt in self.mother_titles_list
        ]
        self.update()

    def handle_title_selected(self, e):
        """Queries the loaded collection tree and dynamically displays matched rows."""
        if not self.title_selector.value:
            self.details_layout.visible = False
            self.update()
            return

        selected_id = int(self.title_selector.value)
        
        # Extract target object reference safely
        mt = next((title for title in self.mother_titles_list if title.id == selected_id), None)
        if not mt:
            return

        # 1. Update Core Metadata Labels
        self.landowner_text.value = mt.landowner.name if mt.landowner else "Unassigned / Unknown"
        self.area_text.value = f"{mt.area_hectares} Hectares"
        
        if mt.barangay and mt.barangay.municipality:
            p_name = mt.barangay.municipality.province.name if mt.barangay.municipality.province else "Unknown Province"
            self.location_text.value = f"{mt.barangay.name}, {mt.barangay.municipality.name}, {p_name}"
        else:
            self.location_text.value = "Geographic bounds not assigned"

        mode = mt.mode_of_acquisition or "N/A"
        lot = f"Lot {mt.lot_number}" if mt.lot_number else "No Lot No."
        survey = f"Survey {mt.survey_number}" if mt.survey_number else "No Survey No."
        self.survey_lot_text.value = f"Mode: {mode} | {lot} ({survey})"

        # 2. Clear out tables for fresh rendering
        self.individual_titles_table.rows.clear()
        self.beneficiaries_table.rows.clear()

        # 3. Populate Individual Titles & ARBs table dynamically if attributes exist
        # Check if the properties exist from the ORM model definitions safely
        sub_titles = getattr(mt, 'individual_titles', [])
        
        for it in sub_titles:
            self.individual_titles_table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(it.title_number or "—", weight=ft.FontWeight.W_500)),
                    ft.DataCell(ft.Text(str(it.area_hectares or "0.0"))),
                    ft.DataCell(ft.Text(it.cloa_number or "Pending")),
                    ft.DataCell(ft.Text(it.status or "Active", color=ft.colors.GREEN_700 if it.status == "Distributed" else ft.colors.BLUE_GREY_600)),
                ])
            )

            # Trace and grab target ARB links attached directly to this specific individual title split segment
            if getattr(it, 'beneficiary', None):
                arb = it.beneficiary
                self.beneficiaries_table.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(arb.name, weight=ft.FontWeight.W_500)),
                        ft.DataCell(ft.Text(it.title_number or "—")),
                        ft.DataCell(ft.Text(str(it.area_hectares or "—"))),
                        ft.DataCell(ft.Text(arb.contact_info if arb.contact_info else "Verified Profile")),
                    ])
                )

        # If no child splits exist yet, show an empty table placeholder row
        if not self.individual_titles_table.rows:
            self.individual_titles_table.rows.append(
                ft.DataRow(cells=[ft.DataCell(ft.Text("No sub-titles split found for this property record.", italic=True)), ft.DataCell(ft.Text("")), ft.DataCell(ft.Text("")), ft.DataCell(ft.Text(""))])
            )
        if not self.beneficiaries_table.rows:
            self.beneficiaries_table.rows.append(
                ft.DataRow(cells=[ft.DataCell(ft.Text("No ARBs allocated to this sub-hierarchy section yet.", italic=True)), ft.DataCell(ft.Text("")), ft.DataCell(ft.Text("")), ft.DataCell(ft.Text(""))])
            )

        # Make the layout view visible and refresh page graphics
        self.details_layout.visible = True
        self.update()
    
