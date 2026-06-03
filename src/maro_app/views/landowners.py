import flet as ft
from src.maro_app.database import get_all_landowners, save_landowner, delete_landowner

class LandownersView(ft.Container):
    def __init__(self):
        # Align perfectly to the top left corner flush with padding
        super().__init__(
            padding=20,
            alignment=ft.alignment.top_left
        )
        self.editing_landowner_id = None  # Tracks if editing an existing profile

        # --- Form Controls (Housed in Dialog Modal) ---
        self.name_input = ft.TextField(
            label="Landowner / Corporate Name", 
            expand=True,
            hint_text="e.g., Juan Dela Cruz or Tagum Agricultural Development Company"
        )
        self.contact_input = ft.TextField(
            label="Contact Information / Address Notes", 
            multiline=True, 
            min_lines=2, 
            max_lines=4, 
            expand=True,
            hint_text="e.g., Contact Number, Official Address, or Representative details"
        )

        # --- Modal Form Action Buttons ---
        self.cancel_btn = ft.TextButton("Cancel", on_click=self.close_form_dialog)
        self.submit_btn = ft.ElevatedButton(
            "Save Profile", 
            bgcolor=ft.colors.BLUE_700, 
            color=ft.colors.WHITE, 
            on_click=self.handle_submit_form
        )

        # --- The Operational Dialog Modal Window ---
        self.form_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Register Landowner Profile", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                width=500,
                height=220,
                content=ft.Column([
                    ft.Row([self.name_input]),
                    ft.Row([self.contact_input]),
                ], spacing=15, scroll=ft.ScrollMode.ALWAYS)
            ),
            actions=[self.cancel_btn, self.submit_btn],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        # --- Master Grid Data Table ---
        self.landowners_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Landowner Name", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Contact Info / Remarks", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Actions", weight=ft.FontWeight.BOLD)),
            ],
            rows=[]
        )

    def did_mount(self):
        # Attach the hidden form dialog structure to the current view page overlays context
        if self.form_dialog not in self.page.overlay:
            self.page.overlay.append(self.form_dialog)

        # Build clean header action layout bar
        header_actions = ft.Row([
            ft.Column([
                ft.Text("Landowners Profiles", size=26, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_GREY_800),
                ft.Text("Manage original private landholders and corporate entities prior to CARP coverage allocation.", size=14, color=ft.colors.GREY_600),
            ]),
            ft.ElevatedButton(
                "Add Landowner",
                icon=ft.icons.ADD,
                bgcolor=ft.colors.BLUE_700,
                color=ft.colors.WHITE,
                on_click=self.open_add_dialog
            )
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        # Main layout structure pushed directly to the top left
        self.content = ft.Column([
            header_actions,
            ft.Divider(height=20),
            ft.Row([self.landowners_table], scroll=ft.ScrollMode.ALWAYS)
        ], 
        alignment=ft.MainAxisAlignment.START,
        scroll=ft.ScrollMode.ALWAYS
        )

        self.refresh_ui_components()

    # --- DIALOG LIFECYCLE MANAGEMENT ---

    def open_add_dialog(self, e):
        """Clears old field memory states and opens a fresh entry form."""
        self.clear_form_fields()
        self.form_dialog.title.value = "Register New Landowner Profile"
        self.submit_btn.text = "Save Profile"
        self.submit_btn.bgcolor = ft.colors.BLUE_700
        self.form_dialog.open = True
        self.page.update()

    def close_form_dialog(self, e=None):
        """Dismisses the modal sheet context."""
        self.form_dialog.open = False
        self.page.update()

    # --- REFRESH CORE ENGINES ---

    def refresh_ui_components(self):
        """Fetches the global inventory list and rebuilds the grid table data rows."""
        landowners = get_all_landowners()

        self.landowners_table.rows.clear()
        for lo in landowners:
            self.landowners_table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(lo.id))),
                    ft.DataCell(ft.Text(lo.name, weight=ft.FontWeight.W_500)),
                    ft.DataCell(ft.Text(lo.contact_info if lo.contact_info else "—")),
                    ft.DataCell(
                        ft.Row([
                            ft.IconButton(
                                ft.icons.EDIT_ROUNDED, 
                                icon_color=ft.colors.BLUE_600, 
                                on_click=lambda e, landowner=lo: self.handle_load_edit(landowner)
                            ),
                            ft.IconButton(
                                ft.icons.DELETE_ROUNDED, 
                                icon_color=ft.colors.RED_400, 
                                on_click=lambda e, id=lo.id: self.handle_delete(id)
                            ),
                        ])
                    )
                ])
            )
        self.update()

    # --- TRANSACTION HANDLERS ---

    def handle_load_edit(self, lo):
        """Loads row entities back into form inputs and pops open the dialog sheet context."""
        self.editing_landowner_id = lo.id
        self.name_input.value = lo.name
        self.contact_input.value = lo.contact_info if lo.contact_info else ""

        self.form_dialog.title.value = f"Modify Landowner Profile: {lo.name}"
        self.submit_btn.text = "Update Profile"
        self.submit_btn.bgcolor = ft.colors.ORANGE_700
        
        self.form_dialog.open = True
        self.page.update()

    def handle_submit_form(self, e):
        name_val = self.name_input.value.strip()
        contact_val = self.contact_input.value.strip()

        if not name_val:
            self.show_snack("Validation Error: Landowner Name is a mandatory field!")
            return

        save_landowner(
            name=name_val,
            contact_info=contact_val if contact_val else None,
            landowner_id=self.editing_landowner_id
        )

        self.close_form_dialog()
        self.show_snack("Landowner registry records successfully updated.")
        self.clear_form_fields()
        self.refresh_ui_components()

    def handle_delete(self, landowner_id):
        delete_landowner(landowner_id)
        self.show_snack("Landowner profile unlinked from database index.")
        self.refresh_ui_components()

    def clear_form_fields(self):
        self.editing_landowner_id = None
        self.name_input.value = ""
        self.contact_input.value = ""

    def show_snack(self, message):
        self.page.overlay.append(ft.SnackBar(ft.Text(message), open=True))
        self.page.update()