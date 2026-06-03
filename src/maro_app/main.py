import flet as ft
from src.maro_app.database import init_db
from src.maro_app.views.dashboard import DashboardView
from src.maro_app.views.mother_titles import MotherTitlesView
from src.maro_app.views.location_management import LocationManagementView
from src.maro_app.views.landowners import LandownersView
from src.maro_app.views.mother_title_details import MotherTitleDetailsView

def main(page: ft.Page):
    page.title = "MARO App | Information System for Land Management and Agrarian Reform in Davao de Oro"
    page.window_width = 1300
    page.window_height = 850
    page.theme_mode = ft.ThemeMode.LIGHT

    init_db()

    # Track sidebar expansion state and selected screen index
    sidebar_expanded = True
    current_index = 0

    # Main content display slot
    content_area = ft.Container(content=DashboardView(), expand=True, padding=20)

    # ---------------------------------------------------------
    # 1. UI Elements Declarations (Declared first to avoid NameErrors)
    # ---------------------------------------------------------
    app_logo = ft.Row(
        [
            ft.Icon(ft.icons.ADD_HOME_ROUNDED, color=ft.colors.BLUE_700, size=24), 
            ft.Text("MARO App", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_900)
        ],
        spacing=8
    )
    
    # We define the toggle function reference below, so we'll assign it right after defining the function
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

    def navigate_to_details(title_id):
        print(f"Navigating to details for {title_id}")
        current_index = 4
        if isinstance(content_area.content, MotherTitleDetailsView):
            content_area.content.load_specific_title(title_id)
        else:
            content_area.content = MotherTitleDetailsView()
            content_area.content.load_specific_title(title_id)
        page.update()

    def navigate_to(index):
        nonlocal current_index
        current_index = index

        for i, wrapper in enumerate(nav_buttons.controls):
            is_selected = i == current_index
            container = wrapper.content
            container.content.controls[0].color = ft.colors.BLUE_700 if is_selected else ft.colors.BLUE_GREY_400
            if len(container.content.controls) > 1:
                container.content.controls[1].color = ft.colors.BLUE_700 if is_selected else ft.colors.BLUE_GREY_700
                container.content.controls[1].weight = ft.FontWeight.BOLD if is_selected else ft.FontWeight.NORMAL
            container.bgcolor = ft.colors.BLUE_100 if is_selected else ft.colors.TRANSPARENT

        if index == 0:
            content_area.content = DashboardView()
        elif index == 1:
            content_area.content = MotherTitlesView(on_view_change=navigate_to_details)
        elif index == 2:
            content_area.content = LocationManagementView()
        elif index == 3:
            content_area.content = LandownersView()
        elif index == 4:
            content_area.content = MotherTitleDetailsView()
        else:
            content_area.content = ft.Container(
                content=ft.Text(f"Management View {index} Coming Soon...", size=18, color=ft.colors.GREY_500),
                alignment=ft.alignment.center,
            )
        page.update()

    # ---------------------------------------------------------
    # 2. Sidebar Navigation Logic & Interaction Functions
    # ---------------------------------------------------------
    def toggle_sidebar(e):
        nonlocal sidebar_expanded
        sidebar_expanded = not sidebar_expanded
        
        # Animate container box constraints
        sidebar_box.width = 240 if sidebar_expanded else 70
        
        # Update alignments & text visibility dynamically
        logo_row.alignment = ft.MainAxisAlignment.SPACE_BETWEEN if sidebar_expanded else ft.MainAxisAlignment.CENTER
        app_logo.visible = sidebar_expanded
        
        # Rebuild navigation item lines to fit state constraints
        render_nav_items()
        page.update()

    # Assign the click handler to the toggle button now that the function is defined
    toggle_btn.on_click = toggle_sidebar

    def route_change(route):
        page.views.clear()
        if page.route == "/mother_title_details":
            target_id = page.session.get("target_title_id")
            details_view = MotherTitleDetailsView()
            details_view.load_specific_title(target_id)
            page.add(details_view)
        # ... handle other routes

    def render_nav_items():
        nav_buttons.controls.clear()
        
        menu_items = [
            (ft.icons.DASHBOARD_ROUNDED, "Dashboard"),
            (ft.icons.LAYERS_ROUNDED, "Mother Titles"),
            (ft.icons.SETTINGS_ACCESSIBILITY_ROUNDED, "Location Settings"),  # <-- Add this line
            (ft.icons.PEOPLE_ROUNDED, "Landowners"),
            (ft.icons.CARD_MEMBERSHIP_ROUNDED, "Individual Titles"),
        ]

        for idx, (icon_name, label_text) in enumerate(menu_items):
            is_active = idx == current_index
            
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

            nav_item = ft.Container(
                content=ft.Row(
                    controls=row_controls,
                    alignment=item_alignment,
                    spacing=12,
                ),
                padding=item_padding,
                border_radius=8,
                bgcolor=ft.colors.BLUE_100 if is_active else ft.colors.TRANSPARENT,
            )

            interactive_wrapper = ft.GestureDetector(
                content=nav_item,
                mouse_cursor=ft.MouseCursor.CLICK,
                on_tap=lambda e, i=idx: navigate_to(i),
            )
            
            nav_buttons.controls.append(interactive_wrapper)

    # Initialize menu rows
    render_nav_items()

    # Master Sidebar Box Structure
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

    # Render Screen Canvas View
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