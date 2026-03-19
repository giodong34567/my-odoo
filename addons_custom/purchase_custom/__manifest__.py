{
    "name": "Purchase Custom",
    "summary": "Quản lý Đề xuất mua sắm",
    "version": "18.0.1.0.0",
    "author": "Custom",
    "license": "LGPL-3",
    "category": "Purchase",
    "depends": [
        "mail",
        "base",
        "purchase",
        "hr",
        "product",
        "stock",
    ],
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "views/purchase_proposal_views.xml",
        "views/purchase_main_menu.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
    "description": """
    Module quản lý đề xuất mua sắm tùy chỉnh.

    Tính năng:
    * Tạo và quản lý đề xuất mua sắm
    * Workflow phê duyệt: Nháp -> Đang duyệt -> Đã duyệt / Từ chối
    * Danh sách sản phẩm đề xuất kèm số lượng, đơn giá
    * Ghi lý do khi từ chối
    * Xem theo danh sách và kanban
    """,
}
