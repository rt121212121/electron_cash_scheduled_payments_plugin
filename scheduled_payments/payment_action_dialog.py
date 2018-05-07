

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from electroncash.i18n import _
from electroncash_gui.qt.util import MessageBoxMixin, Buttons, MyTreeWidget

from .constants import *
from .util import *


class PaymentActionDialog(QDialog, MessageBoxMixin):
    def __init__(self, window, plugin, wallet_name, action, payment_ids):
        # We want to be a top-level window
        QDialog.__init__(self, parent=None)

        self.main_window = window
        self.config = window.config
        self.plugin = plugin
        self.action = action
        self.wallet_name = wallet_name
        self.payment_ids = payment_ids

        self.setMinimumWidth(350)        
        if action == ACTION_FORGET:
            self.setWindowTitle(_("Forget Overdue Payment Occurrences"))
        else:
            self.setWindowTitle(_("Pay Overdue Payment Occurrences"))
            
        formLayout = QFormLayout()
        self.setLayout(formLayout)

        if self.action == ACTION_FORGET:
            action_button_text = _("Forget")
        else:
            action_button_text = _("Pay")
        self.action_button = b = QPushButton(action_button_text)
        b.clicked.connect(self.perform_action)        
        b.setEnabled(False)
        
        self.cancel_button = b = QPushButton(_("Cancel"))
        b.clicked.connect(self.close)
        b.setDefault(True)
        
        self.buttons = [ self.action_button, self.cancel_button ]
        self.summaryLabel = QLabel("Selected total: 0 BCH (0 occurrences)")

        payment_entries = self.plugin.get_wallet_payments(wallet_name)
        self.table = PaymentTable(self, plugin, wallet_name, payment_entries)

        formLayout.addRow(_("Wallet") +':', QLabel(wallet_name))
        formLayout.addRow(self.table)
        
        hbox = QHBoxLayout()
        hbox.addWidget(self.summaryLabel)
        hbox.addStretch(1)
        hbox.addLayout(Buttons(*self.buttons))
        formLayout.addRow(hbox)

    def closeEvent(self, event):
        self.plugin.on_payment_action_window_closed(self.wallet_name)
        event.accept()

    def perform_action(self):
        payment_occurrence_keys = self.table.get_selected_payment_occurrence_keys()
        if self.action == ACTION_FORGET:
            self.plugin.forget_overdue_payment_occurrences(self.wallet_name, payment_occurrence_keys)
            self.close()
        elif self.action == ACTION_PAY:
            self.plugin.prompt_pay_overdue_payment_occurrences(self.wallet_name, payment_occurrence_keys)
            self.close()
        
    def on_items_selected(self, selected_ids):
        self.action_button.setEnabled(len(selected_ids))
        
        payment_entries = self.plugin.get_wallet_payments(self.wallet_name)

        f = ValueFormatter(self.main_window)
        amount = 0.0
        for payment_data in payment_entries:
            for overdue_date in payment_data[PAYMENT_DATESOVERDUE]:
                if (payment_data[PAYMENT_ID], overdue_date) in selected_ids:
                    amount += payment_data[PAYMENT_AMOUNT]
        self.summaryLabel.setText("Selected total: %s (%d occurrences)" % (f.format_value(amount, DISPLAY_AS_AMOUNT), len(selected_ids)))
        


class PaymentTable(MyTreeWidget):
    def __init__(self, parent, plugin, wallet_name, payment_entries):
        self.columns = [ _("Date"), _("Description"), _("Amount"), _("Address") ]

        MyTreeWidget.__init__(self, parent, self.create_menu, self.columns, 0, [])

        self.plugin = plugin
        self.wallet_name = wallet_name
        self.payment_entries = payment_entries

        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSortingEnabled(True)
        self.setMinimumWidth(700)
        
        self.itemSelectionChanged.connect(self.onItemSelectionChanged)
        
        self.applyInitialSelection = True
        self.update()
                
    def on_update(self):
        item = self.currentItem()
        current_id = item.data(0, Qt.UserRole) if item else None
        current_date = item.data(1, Qt.UserRole) if item else None
        self.clear()
        
        rows = self.plugin.get_wallet_payments(self.wallet_name)
        # TODO: Sort?
        
        f = ValueFormatter(self.parent.main_window)

        for payment_data in rows:
            for overdue_date in payment_data[PAYMENT_DATESOVERDUE]:
                values = [
                    f.format_value(overdue_date, DISPLAY_AS_DATETIME),
                    payment_data[PAYMENT_DESCRIPTION],
                    f.format_value(payment_data[PAYMENT_AMOUNT], DISPLAY_AS_AMOUNT),
                    f.format_value(payment_data[PAYMENT_ADDRESS], DISPLAY_AS_ADDRESS),
                ]
                item = QTreeWidgetItem(values)
                item.setData(0, Qt.UserRole, payment_data[PAYMENT_ID])
                item.setData(1, Qt.UserRole, overdue_date)
                item.setData(2, Qt.TextAlignmentRole, Qt.AlignRight | Qt.AlignVCenter) # Align amount to the right.
                self.addTopLevelItem(item)
                if current_id == payment_data[PAYMENT_ID] and current_date == overdue_date:
                    self.setCurrentItem(item)
                if self.applyInitialSelection and payment_data[PAYMENT_ID] in self.parent.payment_ids:
                    item.setSelected(True)

        self.applyInitialSelection = False
                
    def create_menu(self, position):
        pass
        
    def get_selected_payment_occurrence_keys(self):
        selected_items = self.selectedItems()
        selected_ids = [ (item.data(0, Qt.UserRole), item.data(1, Qt.UserRole)) for item in self.selectedItems() ]
        return selected_ids

    def onItemSelectionChanged(self):
        selection_keys = self.get_selected_payment_occurrence_keys()
        self.parent.on_items_selected(selection_keys)

