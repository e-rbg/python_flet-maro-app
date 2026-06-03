import flet as ft
from src.maro_app.database import get_dashboard_data

class DashboardView(ft.Container):
    def __init__(self):
        # Initialize as an expanding layout container
        super().__init__(expand=True, padding=20)
        
        self.data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Landowner", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Mother Title", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Total Area", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Individual Title", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Allocated Area", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Agrarian Reform Beneficiary (ARB)", weight=ft.FontWeight.BOLD)),
            ],
            rows=[],
        )

        self.search_field = ft.TextField(
            hint_text="Search by Landowner, Title Number, or ARB Name...",
            prefix_icon=ft.icons.SEARCH,
            expand=True,
            on_submit=self.handle_search,
            on_change=self.handle_search
        )

    def did_mount(self):
        """Runs automatically right after the control is added to the active canvas page."""
        self.content = ft.Column(
            controls=[
                ft.Row(
                    [
                        ft.Text("Overview Dashboard", size=28, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_GREY_800),
                        ft.IconButton(icon=ft.icons.REFRESH, on_click=self.refresh_data, tooltip="Refresh Data")
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                ft.Divider(height=10, color=ft.colors.TRANSPARENT),
                
                # Search Bar Row
                ft.Row([self.search_field], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(height=15),
                
                # Data Grid Container (Scrollable)
                ft.ListView(
                    controls=[self.data_table],
                    expand=True,
                    spacing=10,
                )
            ],
            expand=True,
            spacing=10,
        )
        # Pull records and draw the lines
        self.load_table_rows()

    def load_table_rows(self, search_term=""):
        """Queries the database and maps values directly to the DataTable UI rows."""
        records = get_dashboard_data(search_term)
        self.data_table.rows.clear()

        for rec in records:
            self.data_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(rec["landowner"])),
                        ft.DataCell(ft.Text(rec["mother_title"], weight=ft.FontWeight.W_500)),
                        ft.DataCell(ft.Text(rec["mother_area"])),
                        ft.DataCell(ft.Text(rec["individual_title"])),
                        ft.DataCell(ft.Text(rec["allocated_area"])),
                        ft.DataCell(ft.Text(rec["arb"], color=ft.colors.BLUE_700 if rec["arb"] not in ["—", "Unassigned"] else ft.colors.BLACK)),
                    ]
                )
            )
        self.update()

    def handle_search(self, e):
        self.load_table_rows(self.search_field.value)

    def refresh_data(self, e):
        self.search_field.value = ""
        self.load_table_rows()