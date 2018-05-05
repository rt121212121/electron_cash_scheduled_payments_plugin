import datetime

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from electroncash.i18n import _
from electroncash_gui.qt.util import MyTreeWidget, MessageBoxMixin

from .constants import *
from .util import *


class ScheduledPaymentsList(MyTreeWidget, MessageBoxMixin):
    def __init__(self, parent, plugin, wallet_name):
        MyTreeWidget.__init__(self, parent, self.create_menu, [
            _('Description'),
            _('Address'),
            _('Amount'),
            _('Last Payment'),
            _('Next Payment'),
        ], 0, [])
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSortingEnabled(True)
        
        self.plugin = plugin
        self.wallet_name = wallet_name

    def create_menu(self, position):
        menu = QMenu()
        selected_items = self.selectedItems()
        selected_payment_ids = [ v.data(0, Qt.UserRole) for v in selected_items ]
        if len(selected_items) == 0: 
            menu.addAction(_("New scheduled payment"), lambda: self.plugin.open_create_payment_dialog(self.wallet_name))
            menu.addAction(_("Toggle clock window"), lambda: self.plugin.toggle_clock_window(self.wallet_name))
        elif len(selected_items) == 1:
            menu.addAction(_("Edit"), lambda: self.plugin.open_edit_payment_dialog(self.wallet_name, selected_items[0].data(0, Qt.UserRole)))
        if len(selected_items) >= 1:
            menu.addAction(_("Delete"), lambda: self.on_delete(selected_payment_ids))
            
        if len(selected_items) and self.plugin.check_payments_overdue(self.wallet_name, selected_payment_ids):
            menu.addAction(_("Pay overdue occurrences"), lambda: self.on_pay_overdue_occurrences(selected_payment_ids))
            menu.addAction(_("Forget overdue occurrences"), lambda: self.on_forget_overdue_occurrences(selected_payment_ids))
                    
        menu.exec_(self.viewport().mapToGlobal(position))
        
    def on_pay_overdue_occurrences(self, payment_ids):
        self.plugin.open_payment_action_window(self.wallet_name, payment_ids, ACTION_PAY)
        
    def on_forget_overdue_occurrences(self, payment_ids):
        self.plugin.open_payment_action_window(self.wallet_name, payment_ids, ACTION_FORGET)
        
    def on_delete(self, selected_ids):
        if self.question(_("Are you sure you want to delete the selected payments?"), title=_("Delete Scheduled Payments")):
            self.plugin.delete_payments(self.wallet_name, selected_ids)

    def on_update(self):
        item = self.currentItem()
        current_key = item.data(0, Qt.UserRole) if item else None
        self.clear()
        
        rows = self.plugin.get_wallet_payments(self.wallet_name)
        # TODO: Sort?
        
        badIcon = QIcon(":icons/status_disconnected.png")
        goodIcon = QIcon(":icons/status_connected.png")

        f = ValueFormatter(self.parent)
        for row in rows:
            row_key = row[PAYMENT_ID]
            values = [
                row[PAYMENT_DESCRIPTION],
                f.format_value(row[PAYMENT_ADDRESS], DISPLAY_AS_ADDRESS),
                f.format_value(row[PAYMENT_AMOUNT], DISPLAY_AS_AMOUNT),
                f.format_value(row[PAYMENT_DATELASTPAID], DISPLAY_AS_DATETIME),
                f.format_value(row[PAYMENT_DATENEXTPAID], DISPLAY_AS_DATETIME),
            ]
            item = QTreeWidgetItem(values)
            if len(row[PAYMENT_DATESOVERDUE]):
                item.setIcon(0, badIcon)
                if len(row[PAYMENT_DATESOVERDUE]) == 1:
                    item.setToolTip(0, _("This scheduled payment has 1 overdue occurrence."))
                else:
                    item.setToolTip(0, _("This scheduled payment has %d overdue occurrences.") % len(row[PAYMENT_DATESOVERDUE]))
            else:
                item.setIcon(0, goodIcon)
                item.setToolTip(0, _("This scheduled payment is up-to-date."))
            item.setData(0, Qt.UserRole, row_key)
            item.setData(2, Qt.TextAlignmentRole, Qt.AlignRight | Qt.AlignVCenter) # Align amount to the right.
            self.addTopLevelItem(item)
            if row_key == current_key:
                self.setCurrentItem(item)

