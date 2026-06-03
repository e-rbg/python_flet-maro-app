import flet as ft
from src.maro_app.database import init_db
from src.maro_app.views.dashboard import DashboardView
from src.maro_app.views.mother_titles import MotherTitlesView
from src.maro_app.views.location_management import LocationManagementView
from src.maro_app.views.landowners import LandownersView
from src.maro_app.views.mother_title_details import MotherTitleDetailsView
from src.maro_app.views.individual_titles import IndividualTitlesView

def main(page: ft.Page):
    page.title = "MARO App | Information System for Land Management and Agrarian Reform in Davao de Oro"
    page.window_width = 1300
    page.window_height = 850
    page.theme_mode = ft.ThemeMode.LIGHT

    # Ensure SQLite context data tables exist
    init_db()

    # App States
    sidebar_expanded = True
    current_index = 0

    # Content Slot Area
    content_area = ft.Container(content=DashboardView(), expand=True, padding=20)

    # --- Header Layout & Toggle Infrastructure ---
    app_logo = ft.Row(
        [
            ft.Icon(ft.icons.ADD_HOME_ROUNDED, color=ft.colors.BLUE_700, size=24), 
            ft.Text("MARO App", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_900)
        ],
        spacing=8
    )
    
    toggle_btn = ft.IconButton(
        icon=ft.icons.MENU_ROUNDED, 
        icon_color=ft.colors.BLUE_GREY_600,
        tooltip="Toggle Menu"
    )

    logo_row = ft.Row(
        controls=[app_logo, toggle_btn],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    nav_buttons = ft.Column(spacing=4)

    # --- Precise View Mapping Core ---
    # Index keys mapping perfectly to your menu array sequence items
    VIEW_MAPPING = {
        0: lambda: DashboardView(),
        1: lambda: MotherTitlesView(on_view_change=navigate_to_details),
        2: lambda: LocationManagementView(),
        3: lambda: LandownersView(),
        4: lambda: IndividualTitlesView(),
        5: lambda: MotherTitleDetailsView()  # Hidden details panel index route
    }

    def navigate_to_details(title_id):
        """Callback to switch directly into the contextual Mother Title inspector."""
        print(f"Navigating to details for {title_id}")
        
        # Explicitly route to details panel index safely
        content_area.content = VIEW_MAPPING[5]()
        content_area.content.load_specific_title(title_id)
        
        # Reset selection highlighters since Details isn't an explicit sidebar row item
        nonlocal current_index
        current_index = 5
        render_nav_items()
        page.update()

    def navigate_to(index: int):
        """Handles top-level view shifting and navigation row highlight updates."""
        nonlocal current_index
        current_index = index

        # Safe programmatic redraw instead of rigid control index mutations
        render_nav_items()

        # Resolve correct constructor execution
        if index in VIEW_MAPPING:
            content_area.content = VIEW_MAPPING[index]()
        else:
            content_area.content = ft.Container(
                content=ft.Text(f"View {index} Under Maintenance...", size=18, color=ft.colors.GREY_500),
                alignment=ft.alignment.center,
            )
        page.update()

    def toggle_sidebar(e):
        nonlocal sidebar_expanded
        sidebar_expanded = not sidebar_expanded
        
        # Smoothly expand or collapse the structural container shell
        sidebar_box.width = 240 if sidebar_expanded else 70
        logo_row.alignment = ft.MainAxisAlignment.SPACE_BETWEEN if sidebar_expanded else ft.MainAxisAlignment.CENTER
        app_logo.visible = sidebar_expanded
        
        render_nav_items()
        page.update()

    toggle_btn.on_click = toggle_sidebar

    def render_nav_items():
        """Redraws sidebar elements cleanly based on position and active state indexes."""
        nav_buttons.controls.clear()
        
        menu_items = [
            (ft.icons.DASHBOARD_ROUNDED, "Dashboard"),
            (ft.icons.LAYERS_ROUNDED, "Mother Titles"),
            (ft.icons.SETTINGS_ACCESSIBILITY_ROUNDED, "Location Settings"),
            (ft.icons.PEOPLE_ROUNDED, "Landowners"),
            (ft.icons.CARD_MEMBERSHIP_ROUNDED, "Individual Titles"), # Row Index 4 matches view map perfectly!
        ]

        for idx, (icon_name, label_text) in enumerate(menu_items):
            is_active = (idx == current_index)
            
            row_controls = [
                ft.Icon(
                    name=icon_name, 
                    color=ft.colors.BLUE_700 if is_active else ft.colors.BLUE_GREY_400,
                    size=22
                )
            ]
            
            if sidebar_expanded:
                row_controls.append(
                    ft.Text(
                        value=label_text, 
                        color=ft.colors.BLUE_700 if is_active else ft.colors.BLUE_GREY_700,
                        weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL,
                        size=14
                    )
                )
                item_alignment = ft.MainAxisAlignment.START
                item_padding = ft.padding.symmetric(horizontal=16, vertical=12)
            else:
                item_alignment = ft.MainAxisAlignment.CENTER
                item_padding = ft.padding.symmetric(vertical=12)

            # Using InkWell gives modern splash responses when buttons are clicked
            #  The correct Flet implementation
            nav_item = ft.Container(
                content=ft.Row(
                    controls=row_controls,
                    alignment=item_alignment,
                    spacing=12,
                ),
                padding=item_padding,
                border_radius=8,
                bgcolor=ft.colors.BLUE_50 if is_active else ft.colors.TRANSPARENT,
                # Move the click event handler directly onto the Container
                on_click=lambda e, i=idx: navigate_to(i)
                
            )
            nav_buttons.controls.append(nav_item)

    # Initial Sidebar Menu Synthesis
    render_nav_items()

    # Master Left Sidebar Panel
    sidebar_box = ft.Container(
        width=240,
        bgcolor=ft.colors.GREY_50,
        padding=ft.padding.only(left=12, top=16, right=12, bottom=16),
        animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT_CUBIC),
        content=ft.Column(
            controls=[
                logo_row,
                ft.Divider(height=20, color=ft.colors.GREY_200),
                nav_buttons
            ],
            spacing=10
        )
    )

    # Mount UI Canvas Elements onto Page Surface
    page.add(
        ft.Row(
            [
                sidebar_box,
                ft.VerticalDivider(width=1, color=ft.colors.GREY_200),
                content_area
            ],
            expand=True
        ),
    )

if __name__ == "__main__":
    ft.app(target=main)