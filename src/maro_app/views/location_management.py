import flet as ft
from src.maro_app.database import (
    get_all_provinces, add_province, delete_province,
    get_all_municipalities_global, add_municipality, delete_municipality,
    get_all_barangays_global, add_barangay, delete_barangay
)


class LocationManagementView(ft.Container):
    def __init__(self):
        super().__init__(padding=20)
        
        # --- Form Text Inputs ---
        self.prov_name_input = ft.TextField(label="New Province Name", expand=True, on_submit=self.handle_add_province)
        self.mun_name_input = ft.TextField(label="New Municipality Name", expand=True, on_submit=self.handle_add_municipality)
        self.bar_name_input = ft.TextField(label="New Barangay Name", expand=True, on_submit=self.handle_add_barangay)
        
        # --- Context Parent Entry Selectors ---
        self.prov_selector_for_mun = ft.Dropdown(label="Province Name", expand=True)
        self.mun_selector_for_bar = ft.Dropdown(label="Municipality Name", expand=True)

        # --- Dynamic Global Tables ---
        self.prov_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID", weight=ft.FontWeight.BOLD)), 
                ft.DataColumn(ft.Text("Province Name", weight=ft.FontWeight.BOLD)), 
                ft.DataColumn(ft.Text("Action", weight=ft.FontWeight.BOLD))
            ],
            rows=[]
        )
        self.mun_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID", weight=ft.FontWeight.BOLD)), 
                ft.DataColumn(ft.Text("Municipality Name", weight=ft.FontWeight.BOLD)), 
                ft.DataColumn(ft.Text("Parent Province Location", weight=ft.FontWeight.BOLD)), 
                ft.DataColumn(ft.Text("Action", weight=ft.FontWeight.BOLD))
            ],
            rows=[]
        )
        self.bar_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID", weight=ft.FontWeight.BOLD)), 
                ft.DataColumn(ft.Text("Barangay Name", weight=ft.FontWeight.BOLD)), 
                ft.DataColumn(ft.Text("Parent Administrative Hierarchy Context", weight=ft.FontWeight.BOLD)), 
                ft.DataColumn(ft.Text("Action", weight=ft.FontWeight.BOLD))
            ],
            rows=[]
        )

    def did_mount(self):
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=200,
            tabs=[
                ft.Tab(text="Provinces Inventory", icon=ft.icons.MAP, content=self.build_province_tab()),
                ft.Tab(text="Municipalities Inventory", icon=ft.icons.LOCATION_CITY, content=self.build_municipality_tab()),
                ft.Tab(text="Barangays Inventory", icon=ft.icons.HOME_ROUNDED, content=self.build_barangay_tab()),
            ],
            on_change=self.handle_tab_switch
        )
        
        self.content = ft.Column([
            ft.Text("Geographic Registry Settings", size=26, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_GREY_800),
            ft.Text("Master system indexes for geo-mapping distribution rules.", size=14, color=ft.colors.GREY_600),
            ft.Divider(height=15),
            self.tabs
        ], scroll=ft.ScrollMode.ALWAYS)
        
        self.preload_all_system_components()

    # --- TAB DESIGN LAYOUT BUILDERS ---

    def build_province_tab(self):
        return ft.Container(
            padding=ft.padding.symmetric(vertical=15),
            content=ft.Column([
                ft.Row([
                    self.prov_name_input,
                    ft.ElevatedButton("Register Province", icon=ft.icons.ADD, bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE, on_click=self.handle_add_province)
                ]),
                ft.Divider(height=15, color=ft.colors.TRANSPARENT),
                self.prov_table
            ])
        )

    def build_municipality_tab(self):
        return ft.Container(
            padding=ft.padding.symmetric(vertical=15),
            content=ft.Column([
                ft.Row([
                    self.prov_selector_for_mun,
                    self.mun_name_input,
                    ft.ElevatedButton("Register Municipality", icon=ft.icons.ADD, bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE, on_click=self.handle_add_municipality)
                ]),
                ft.Divider(height=15, color=ft.colors.TRANSPARENT),
                self.mun_table
            ])
        )

    def build_barangay_tab(self):
        return ft.Container(
            padding=ft.padding.symmetric(vertical=15),
            content=ft.Column([
                ft.Row([
                    self.mun_selector_for_bar,
                    self.bar_name_input,
                    ft.ElevatedButton("Register Barangay", icon=ft.icons.ADD, bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE, on_click=self.handle_add_barangay)
                ]),
                ft.Divider(height=15, color=ft.colors.TRANSPARENT),
                self.bar_table
            ])
        )

    # --- REFRESH CORE ENGINES ---

    def preload_all_system_components(self):
        """Unified reload that updates current lists and forms simultaneously."""
        provinces = get_all_provinces()
        municipalities = get_all_municipalities_global()
        barangays = get_all_barangays_global()

        # Update input form dropdown indexes
        self.prov_selector_for_mun.options = [ft.dropdown.Option(key=str(p.id), text=p.name) for p in provinces]
        self.mun_selector_for_bar.options = [
            ft.dropdown.Option(
                key=str(m.id), 
                text=f"{m.name} ({m.province.name})" if m.province else f"{m.name} (Unknown Province)"
            ) for m in municipalities
        ]

        # 1. Rebuild Provinces Table
        self.prov_table.rows.clear()
        for p in provinces:
            self.prov_table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(p.id))),
                    ft.DataCell(ft.Text(p.name, weight=ft.FontWeight.W_500)),
                    ft.DataCell(ft.IconButton(ft.icons.DELETE_OUTLINE_ROUNDED, icon_color=ft.colors.RED_400, on_click=lambda e, id=p.id: self.handle_delete_prov(id)))
                ])
            )

        # 2. Rebuild Municipalities Table (with parent labels)
        self.mun_table.rows.clear()
        for m in municipalities:
            prov_name = m.province.name if m.province else "Unassigned"
            
            self.mun_table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(m.id))),
                    ft.DataCell(ft.Text(m.name, weight=ft.FontWeight.W_500)),
                    ft.DataCell(ft.Text(prov_name, style=ft.TextStyle(color=ft.colors.BLUE_700, weight=ft.FontWeight.W_500))),
                    ft.DataCell(ft.IconButton(ft.icons.DELETE_OUTLINE_ROUNDED, icon_color=ft.colors.RED_400, on_click=lambda e, id=m.id: self.handle_delete_mun(id)))
                ])
            )

        # 3. Rebuild Barangays Table (Independent full list regardless of filtering state)
        self.bar_table.rows.clear()
        for b in barangays:
            # FIXED: Bulletproof handling of nested parent strings to prevent AttributeError
            if b.municipality:
                p_name = b.municipality.province.name if b.municipality.province else "Unknown Province"
                parent_lineage = f"{b.municipality.name}, {p_name}"
            else:
                parent_lineage = "—"
            
            self.bar_table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(b.id))),
                    ft.DataCell(ft.Text(b.name, weight=ft.FontWeight.W_500)),
                    ft.DataCell(ft.Text(parent_lineage, size=13)),
                    ft.DataCell(ft.IconButton(ft.icons.DELETE_OUTLINE_ROUNDED, icon_color=ft.colors.RED_400, on_click=lambda e, id=b.id: self.handle_delete_bar(id)))
                ])
            )
        self.update()

    def handle_tab_switch(self, e):
        self.preload_all_system_components()

    # --- TRANSACTIONAL ACTION HANDLERS ---

    def handle_add_province(self, e):
        name = self.prov_name_input.value.strip()
        if name:
            add_province(name)
            self.prov_name_input.value = ""
            self.preload_all_system_components()
            self.show_snack(f"Province '{name}' successfully cached.")

    def handle_add_municipality(self, e):
        if not self.prov_selector_for_mun.value:
            self.show_snack("Validation Error: Please match to a parent Province lineage choice first!")
            return
        name = self.mun_name_input.value.strip()
        if name:
            add_municipality(name, int(self.prov_selector_for_mun.value))
            self.mun_name_input.value = ""
            self.preload_all_system_components()
            self.show_snack(f"Municipality '{name}' added.")

    def handle_add_barangay(self, e):
        if not self.mun_selector_for_bar.value:
            self.show_snack("Validation Error: Please map to a specific target Municipality entry!")
            return
        name = self.bar_name_input.value.strip()
        if name:
            add_barangay(name, int(self.mun_selector_for_bar.value))
            self.bar_name_input.value = ""
            self.preload_all_system_components()
            self.show_snack(f"Barangay '{name}' added.")

    def handle_delete_prov(self, prov_id):
        delete_province(prov_id)
        self.preload_all_system_components()
        self.show_snack("Province item unlinked.")

    def handle_delete_mun(self, m_id):
        delete_municipality(m_id)
        self.preload_all_system_components()
        self.show_snack("Municipality element popped.")

    def handle_delete_bar(self, b_id):
        delete_barangay(b_id)
        self.preload_all_system_components()
        self.show_snack("Barangay element popped.")

    def show_snack(self, message):
        self.page.overlay.append(ft.SnackBar(ft.Text(message), open=True))
        self.page.update()