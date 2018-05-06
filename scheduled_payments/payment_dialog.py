import datetime

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from electroncash import bitcoin
from electroncash.address import Address
from electroncash.i18n import _
from electroncash_gui.qt.util import MessageBoxMixin, Buttons, HelpLabel
from electroncash_gui.qt.amountedit import MyLineEdit, BTCAmountEdit
from electroncash_gui.qt.paytoedit import PayToEdit
import electroncash.web as web

from .constants import *

class PaymentDialog(QDialog, MessageBoxMixin):
    def __init__(self, window, plugin, payment_data):
        # We want to be a top-level window
        QDialog.__init__(self, parent=None)

        #print("PaymentDialog", "payment_data =", payment_data)
        self.payment_data = payment_data
        
        self.plugin = plugin

        # WARNING: Copying some attributes so PayToEdit() will work.
        self.main_window = window
        self.contacts = self.main_window.contacts
        self.is_max = self.main_window.is_max # Unused, as we do not use max.
        self.completions = self.main_window.completions

        self.count_labels = [
            "Disabled",
            "Once",
            "Always",
        ]
        self.display_count_labels = [
            "Always",
        ]
        run_always_index = self.count_labels.index("Always")

        # NOTE: User entered data, for verification purposes (enabling save/create), and subsequent dispatch on button press.
        self.value_description = ""
        self.value_amount = None
        self.value_payto_outputs = []
        self.value_run_occurrences = self.count_labels.index("Always")
        
        if self.payment_data is not None:
            self.value_description = self.payment_data[PAYMENT_DESCRIPTION]
            self.value_amount = self.payment_data[PAYMENT_AMOUNT]
            self.value_run_occurrences = self.payment_data[PAYMENT_COUNT0]
        
        # NOTE: Set up the UI for this dialog.
        self.setMinimumWidth(350)        
        if payment_data is None:
            self.setWindowTitle(_("Create New Scheduled Payment"))
        else:
            self.setWindowTitle(_("Edit Existing Scheduled Payment"))
            
        formLayout = QFormLayout()
        self.setLayout(formLayout)
        
        # Input fields.
        msg = _('Description of the payment (not mandatory).') + '\n\n' + _('The description is not sent to the recipient of the funds. It is stored in your wallet file, and displayed in the \'History\' tab.')
        self.description_label = HelpLabel(_('Description'), msg)
        self.description_edit = MyLineEdit()
        self.description_edit.setText(self.value_description)
        formLayout.addRow(self.description_label, self.description_edit)
        
        msg = _('How much to pay.') + '\n\n' + _('Unhelpful descriptive text')
        self.amount_label = HelpLabel(_('Amount'), msg)
        self.amount_e = BTCAmountEdit(window.get_decimal_point) # WARNING: This has to be named this, as PayToEdit accesses it.
        self.amount_e.setAmount(self.value_amount)
        # WARNING: This needs to be present before PayToEdit is constructed (as that accesses it's attribute on this object),
        # but added to the layout after in order to try and reduce the "cleared amount" problem that happens when an address
        # is entered (perhaps on a selected completion, i.e. of a contact).
        
        # WARNING: This will clear the amount when an address is set, see PayToEdit.check_text.
        self.payto_edit = PayToEdit(self)
        msg = _('Recipient of the funds.') + '\n\n' + _('You may enter a Bitcoin Cash address, a label from your list of contacts (a list of completions will be proposed), or an alias (email-like address that forwards to a Bitcoin Cash address)')
        payto_label = HelpLabel(_('Pay to'), msg)
        formLayout.addRow(payto_label, self.payto_edit)
        def set_payment_address(address):
            self.payto_edit.payto_address = bitcoin.TYPE_ADDRESS, Address.from_string(address)
            self.value_payto_outputs = self.payto_edit.get_outputs(False)
            contact_name = None
            if address in window.wallet.contacts.keys():
                contact_type, contact_name = window.wallet.contacts[address]
            if contact_name is not None:
                self.payto_edit.setText(contact_name +' <'+ address +'>')
            else:
                self.payto_edit.setText(address)                
        if payment_data is not None:
            set_payment_address(payment_data[PAYMENT_ADDRESS])

        completer = QCompleter()
        completer.setCaseSensitivity(False)
        self.payto_edit.setCompleter(completer)
        completer.setModel(self.completions)

        # WARNING: We created this before PayToEdit and add it to the layout after, due to the dependency issues with PayToEdit accessing `self.amount_e`.
        formLayout.addRow(self.amount_label, self.amount_e)
        
        if payment_data is not None:
            text = _("No payments made.")
            if payment_data[PAYMENT_DATELASTPAID] is not None:
                text = datetime.datetime.fromtimestamp(payment_data[PAYMENT_DATELASTPAID]).strftime("%c")
            textLabel = QLabel(text)
            label = HelpLabel(_('Last Paid'), _('Date last paid.') + '\n\n' + _('The date at which this scheduled payment was last meant to send a transaction to the network, which the user acted on'))
            formLayout.addRow(label, textLabel)
            
        count_combo = QComboBox()
        count_combo.addItems(self.display_count_labels)
        count_combo.setCurrentIndex(self.display_count_labels.index(self.count_labels[self.value_run_occurrences]))
        msg = _('Run occurrences.') + '\n\n' + _('The number of times the payment should be made.')
        label = HelpLabel(_('Run occurrences'), msg)
        formLayout.addRow(label, count_combo)

        import importlib
        from . import when_widget
        importlib.reload(when_widget)
        self.whenWidget = when_widget.WhenWidget(_("When"))
        self.whenWidget.setWhen(None if payment_data is None else payment_data[PAYMENT_WHEN])
        formLayout.addRow(self.whenWidget)

        # NOTE: Hook up value events and provide handlers.
        
        def validate_input_values():
            allow_commit = True
            allow_commit = allow_commit and len(self.value_description) > 0
            allow_commit = allow_commit and self.value_amount is not None and self.value_amount > 0
            allow_commit = allow_commit and len(self.value_payto_outputs) > 0
            allow_commit = allow_commit and self.value_run_occurrences == run_always_index
            # allow_commit = allow_commit and self.value_run_occurrences > -1 and self.value_run_occurrences < len(count_labels)
            self.save_button.setEnabled(allow_commit)
                
        def on_run_occurrences_changed(unknown):
            self.value_run_occurrences = self.count_labels.index(self.display_count_labels[count_combo.currentIndex()])
            validate_input_values()
        count_combo.currentIndexChanged.connect(on_run_occurrences_changed)

        def on_recipient_changed():
            self.value_payto_outputs = self.payto_edit.get_outputs(False)
            validate_input_values()
        self.payto_edit.textChanged.connect(on_recipient_changed)
        
        def on_amount_changed():
            self.value_amount = self.amount_e.get_amount()
            validate_input_values()
        self.amount_e.textChanged.connect(on_amount_changed)

        def on_description_changed():
            self.value_description = self.description_edit.text().strip()
            validate_input_values()
        self.description_edit.textChanged.connect(on_description_changed)
        
        # Buttons at bottom right.
        save_button_text = _("Save")
        if payment_data is None:
            save_button_text = _("Create")
        self.save_button = b = QPushButton(save_button_text)
        b.clicked.connect(self.save)

        self.cancel_button = b = QPushButton(_("Cancel"))
        b.clicked.connect(self.close)
        b.setDefault(True)

        self.buttons = [self.save_button, self.cancel_button]
        
        hbox = QHBoxLayout()
        #hbox.addLayout(Buttons(*self.sharing_buttons))
        hbox.addStretch(1)
        hbox.addLayout(Buttons(*self.buttons))
        formLayout.addRow(hbox)

        validate_input_values()
        self.update()
        
    def save(self):
        # NOTE: This is in lieu of running some kind of updater that updates the esetimated time every second.
        if self.whenWidget.updateEstimatedTime():
            if not self.question(_("The next matching date passed between the last time you modified the date, and when you clicked on save.  Do you wish to proceed anyway?"), title=_("Next Matching Date Changed")):
                return
    
        data_id = None
        if self.payment_data is not None:
            data_id = self.payment_data[PAYMENT_ID]
            
        payment_data = [ None ] * PAYMENT_ENTRY_LENGTH
        payment_data[PAYMENT_ID] = data_id
        payment_data[PAYMENT_ADDRESS] = self.value_payto_outputs[0][1].to_storage_string()
        payment_data[PAYMENT_AMOUNT] = self.value_amount
        payment_data[PAYMENT_DESCRIPTION] = self.value_description
        payment_data[PAYMENT_COUNT0] = self.value_run_occurrences
        payment_data[PAYMENT_WHEN] = self.whenWidget.getWhen().toText()
        payment_data[PAYMENT_DATENEXTPAID] = self.whenWidget.getEstimatedTime()
        
        wallet_name = self.main_window.wallet.basename()
        self.plugin.update_payment(wallet_name, payment_data)
        
        self.close()
        
    def closeEvent(self, event):
        wallet_name = self.main_window.wallet.basename()
        if self.payment_data is None:
            payment_id = None
        else:
            payment_id = self.payment_data[PAYMENT_ID]
        self.plugin.on_payment_editor_closed(wallet_name, payment_id)
        event.accept()
        
    def onTimeChanged(self, clock_current_time):
        self.whenWidget.updateEstimatedTime(currentTime=clock_current_time)

    def lock_amount(self, flag): # WARNING: Copied as needed for PayToEdit
        self.amount_e.setFrozen(flag)
        
    def do_update_fee(self): # WARNING: Copied as needed for PayToEdit
        pass

    def pay_to_URI(self, URI): # WARNING: Copied as needed for PayToEdit
        if not URI:
            return
        try:
            out = web.parse_URI(URI, self.on_pr)
        except Exception as e:
            self.show_error(_('Invalid bitcoincash URI:') + '\n' + str(e))
            return
        r = out.get('r')
        sig = out.get('sig')
        name = out.get('name')
        if r or (name and sig):
            self.prepare_for_payment_request()
            return
        address = out.get('address')
        amount = out.get('amount')
        label = out.get('label')
        message = out.get('message')
        # use label as description (not BIP21 compliant)
        if label and not message:
            message = label
        if address:
            self.payto_edit.setText(address)
        if message:
            self.description_edit.setText(message)
        if amount:
            self.amount_e.setAmount(amount)
            self.amount_e.textEdited.emit("")

    def prepare_for_payment_request(self): # WARNING: Copied as needed for PayToEdit
        self.payto_edit.is_pr = True
        for e in [self.payto_edit, self.amount_e, self.description_edit]:
            e.setFrozen(True)
        self.payto_edit.setText(_("please wait..."))
        return True
