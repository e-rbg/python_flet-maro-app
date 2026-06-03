import flet as ft

class MotherTitleDetailsView(ft.Container):
    def __init__(self):
        super().__init__(padding=15)
        # ✅ This belongs HERE, inside MotherTitleDetailsView!
        self.title_text = ft.Text(size=22, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_900)
        self.owner_text = ft.Text(size=16, weight=ft.FontWeight.W_500)
        self.area_text = ft.Text(size=16)
        self.acquisition_text = ft.Text(size=16)
        self.lot_survey_text = ft.Text(size=16)
        self.location_text = ft.Text(size=16, color=ft.colors.BLUE_GREY_700)
        
        self.raw_text_field = ft.TextField(label="Technical Metadata", multiline=True, read_only=True, expand=True)
        self.lines_field = ft.TextField(label="Boundary Coordinates", multiline=True, read_only=True, expand=True)
        
        self.content = ft.Text("Select a title.")

    def preload_titles_dropdown(self):
        """Kept purely to preserve structural backwards compatibility with workspace views"""
        pass

    def load_specific_title(self, mt):
        """
        Accepts the rich database model object sent directly from your master data table 
        row selection and maps it to the tracking interface layout.
        """
        if not mt:
            return

        # Assign values directly to tracking variables
        self.title_text.value = f"OCT / TCT No: {mt.title_number or 'N/A'}"
        self.owner_text.value = f"{mt.landowner.name if mt.landowner else 'Unknown Landowner Record'}"
        self.area_text.value = f"{mt.area_hectares} Hectares"
        self.acquisition_text.value = f"{mt.mode_of_acquisition or '—'}"
        self.lot_survey_text.value = f"{mt.lot_number or '—'} | Survey {mt.survey_number or '—'}"
        
        # Safely resolve deep nested geography paths
        if mt.barangay and mt.barangay.municipality:
            prov = mt.barangay.municipality.province.name if mt.barangay.municipality.province else "Unknown Province"
            self.location_text.value = f"Jurisdiction: Brgy. {mt.barangay.name}, {mt.barangay.municipality.name}, {prov}"
        elif mt.barangay:
            self.location_text.value = f"Jurisdiction: Brgy. {mt.barangay.name} (Unlinked)"
        else:
            self.location_text.value = "Jurisdiction Index: Geographic Location Unrecorded"

        self.raw_text_field.value = mt.raw_text or "No technical descriptive deed narrative logs recorded for this record."
        self.lines_field.value = mt.lines or "No boundary line traversal paths mapped."
        
        # Inject the active layout matrix into our root container shell
        self.content = ft.Column([
            self.title_text,
            ft.Divider(color=ft.colors.BLUE_400, height=2),
            ft.Container(height=10),
            ft.Row([
                # Left Core Summary Column Block
                ft.Container(
                    expand=5,
                    content=ft.Column([
                        ft.ListTile(
                            leading=ft.Icon(ft.icons.PERSON_PIN_ROUNDED, color=ft.colors.BLUE_700, size=28), 
                            title=self.owner_text, 
                            subtitle=ft.Text("Registered Landowner")
                        ),
                        ft.ListTile(
                            leading=ft.Icon(ft.icons.LANDSCAPE_ROUNDED, color=ft.colors.GREEN_700, size=28), 
                            title=self.area_text, 
                            subtitle=ft.Text("Area")
                        ),
                        ft.ListTile(
                            leading=ft.Icon(ft.icons.ASSIGNMENT_ROUNDED, color=ft.colors.ORANGE_700, size=28), 
                            title=self.acquisition_text, 
                            subtitle=ft.Text("Mode of Acquisition")
                        ),
                        ft.ListTile(
                            leading=ft.Icon(ft.icons.MAP_ROUNDED, color=ft.colors.PURPLE_700, size=28), 
                            title=self.lot_survey_text, 
                            subtitle=ft.Text("Lot Number & Survey Number")
                        ),
                        ft.ListTile(
                            leading=ft.Icon(ft.icons.PIN_DROP_ROUNDED, color=ft.colors.RED_700, size=28), 
                            title=self.location_text, 
                            subtitle=ft.Text("Location")
                        ),
                    ], spacing=10)
                ),
                # Vertical Divider between processing zones
                ft.VerticalDivider(width=2, color=ft.colors.GREY_200),
                # Right Advanced Legal Text Log Block
                ft.Container(
                    expand=6,
                    content=ft.Column([
                        self.raw_text_field,
                        ft.Container(height=10),
                        self.lines_field
                    ], alignment=ft.MainAxisAlignment.START, spacing=5)
                )
            ], alignment=ft.MainAxisAlignment.START, cross_axis_alignment=ft.CrossAxisAlignment.START, expand=True)
        ], scroll=ft.ScrollMode.ADAPTIVE, expand=True)
        self.update()
        