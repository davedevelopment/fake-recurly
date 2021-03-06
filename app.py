from flask import Flask, url_for, request, render_template, redirect
from xml.etree.ElementTree import ElementTree, fromstring
from fakerecurly.models import *
from fakerecurly.errors import *
from operator import attrgetter
import time
import sys

app = Flask(__name__)

@app.route("/", methods=["DELETE"])
def teardown():
    print "Tearing down data"
    Invoice.truncate();
    Transaction.truncate()
    Subscription.truncate()
    Account.truncate()
    Plan.truncate()
    return "", 204

@app.errorhandler(NotFoundError)
def resource_not_found(error):
    print "error: %s" % error
    return render_template("error.xml", error=error), 404

# COUPONS

@app.route("/coupons", methods=["POST"])
def post_coupon():
    tree = fromstring(request.data)
    coupon = Coupon.fromTree(tree)
    print "Creating coupon:%s" % (coupon.couponCode)
    Coupon.save(coupon)
    return render_template("coupon.xml", coupon=coupon), 201


# SUBSCRIPTIONS

@app.route("/subscriptions", methods=["POST"])
def create_subscription():
    tree = fromstring(request.data)
    sub = Subscription.fromTree(tree)

    if not Account.find(sub.accountCode):
        account = Account(sub.accountCode)
        print "Creating account:%s" % (account.accountCode)
        Account.save(account)

    plan = find_plan_or_404(sub.planCode)

    print "Creating subscription:%s" % (sub.uuid)
    Subscription.save(sub)

    trans = Transaction()
    trans.accountCode = sub.accountCode
    trans.subscriptionUuid = sub.uuid
    print "Creating transaction:%s" % (trans.uuid)
    Transaction.save(trans)

    return render_template("subscription.xml", subscription=sub, account=Account.find(sub.accountCode), plan=Plan.find(sub.planCode)), 201

def find_subscription_or_404(uuid):
    sub = Subscription.find(uuid)
    if not sub:
        raise NotFoundError("Couldn't find Subscription with uuid = %s" % uuid)
    return sub

# Not part of the official API, used to manage state while testing
@app.route("/subscriptions/<uuid>/state", methods=["POST"])
def set_subscription_status(uuid):
    sub = find_subscription_or_404(uuid)
    sub.state = request.form['state']
    Subscription.save(sub)
    return get_subscription(uuid)

# Not part of the official API, used to manage state while testing
@app.route("/subscriptions/<uuid>/past_due", methods=["POST"])
def set_subscription_past_due(uuid):
    sub = find_subscription_or_404(uuid)
    sub.past_due = bool(request.form['past_due'])
    Subscription.save(sub)
    return get_subscription(uuid)

# Not part of the official API, used to generate a new transaction
@app.route("/subscriptions/<uuid>/bill", methods=["POST"])
def generate_bill_for_subscription(uuid):
    sub = find_subscription_or_404(uuid)
    trans = Transaction()
    trans.accountCode = sub.accountCode
    trans.subscriptionUuid = sub.uuid
    try:
        trans.status = request.form['status']
    except KeyError:
        trans.status = 'success'
    try:
        trans.action = request.form['action']
    except KeyError:
        trans.action = 'purchase'
    print "Creating transaction:%s" % (trans.uuid)
    Transaction.save(trans)
    return get_transaction(trans.uuid)

@app.route("/subscriptions/<uuid>/cancel", methods=["PUT"])
def cancel_subscription(uuid):
    sub = find_subscription_or_404(uuid)
    sub.state = "canceled"
    Subscription.save(sub)
    return get_subscription(uuid)

@app.route("/subscriptions/<uuid>/terminate", methods=["PUT"])
def terminate_subscription(uuid):
    sub = find_subscription_or_404(uuid)
    sub.state = "expired"
    Subscription.save(sub)
    return get_subscription(uuid)

@app.route("/subscriptions/<uuid>", methods=["GET"])
def get_subscription(uuid):
    sub = find_subscription_or_404(uuid)
    plan = Plan.find(sub.planCode)
    account = Account.find(sub.accountCode)
    return render_template("subscription.xml", subscription=sub, account=account, plan=plan), 200

# TRANSACTIONS
@app.route("/transactions/<uuid>", methods=["GET"])
def get_transaction(uuid):
    if not Transaction.find(uuid):
        raise NotFoundError("Couldn't find transaction with uuid = %s" % uuid)
    return render_template("transaction.xml", transaction=Transaction.find(uuid)), 200

@app.route("/transactions/<uuid>/subscriptions", methods=["GET"])
def get_transactions_subscriptions(uuid):
    if not Transaction.find(uuid):
        raise NotFoundError("Couldn't find transaction with uuid = %s" % uuid)
    transaction=Transaction.find(uuid)
    subscription = Subscription.find(transaction.subscriptionUuid)
    return render_template("subscriptions.xml", subscriptions={subscription.uuid: subscription}), 200

# Not part of the official API, used to manage state while testing
@app.route("/transactions/<uuid>/status", methods=["POST"])
def set_transaction_status(uuid):
    trans = Transaction.find(uuid)
    if not trans:
        raise NotFoundError("Couldn't find transaction with uuid = %s" % uuid)
    trans.status = request.form['status']
    Transaction.save(trans)
    return get_transaction(uuid)

# Not part of the official API, used to manage recurring flag while testing
@app.route("/transactions/<uuid>/recurring", methods=["POST"])
def set_transaction_recurring(uuid):
    trans = Transaction.find(uuid)
    if not trans:
        raise NotFoundError("Couldn't find transaction with uuid = %s" % uuid)
    trans.recurring = bool(int(request.form['recurring']))
    Transaction.save(trans)
    return get_transaction(uuid)

#INVOICES

# Not part of the official API, used to generate a new invoice
@app.route("/accounts/<accountCode>/stubinvoices", methods=["POST"])
def generate_invoice_for_account(accountCode):
    acc = find_account_or_404(accountCode)
    invoice = Invoice(accountCode)
    try:
        invoice.state = request.form['state']
    except KeyError:
        invoice.state = 'open'
    print "Creating Invoice:%s" % (invoice.uuid)
    Invoice.save(invoice)
    return "", 201

@app.route("/accounts/<accountCode>/invoices", methods=["GET"])
def get_account_invoices(accountCode):
    find_account_or_404(accountCode) 
    invoices = Invoice.findByAccount(accountCode)    
    xml = render_template("invoices.xml", invoices=invoices)
    return xml, 200, { "X-Records": len(invoices) }

@app.route("/invoices/<invoiceNumber>/mark_failed", methods=["PUT", "POST"])
def mark_invoice_failed(invoiceNumber):
    inv = Invoice.findByInvoiceNumber(invoiceNumber)
    inv.state = 'failed';
    Invoice.save(inv);
    xml = render_template("invoice_collection.xml", invoices={inv.uuid: inv})
    return xml, 201

# ACCOUNTS

def find_account_or_404(accountCode):
    acc = Account.find(accountCode)
    if not acc:
        raise NotFoundError("Couldn't find Account with account_code = %s" % accountCode)
    return acc

@app.route("/accounts/<accountCode>", methods=["GET"])
def get_account(accountCode):
    acc = find_account_or_404(accountCode) 
    return render_template("account.xml", account=acc), 200

@app.route("/accounts/<accountCode>/transactions", methods=["GET"])
def get_account_transactions(accountCode):
    find_account_or_404(accountCode) 
    transactions = Transaction.findByAccount(accountCode)    
    transactions = sorted(transactions.values(), key=attrgetter('created'))
    return render_template("transactions.xml", transactions=transactions), 200

@app.route("/accounts/<accountCode>/subscriptions", methods=["GET"])
def get_account_subscriptions(accountCode):
    find_account_or_404(accountCode) 
    state = request.args.get('state', False)
    subscriptions = Subscription.findByAccount(accountCode, state)    
    return render_template("subscriptions.xml", subscriptions=subscriptions), 200, { "X-Records": len(subscriptions) }

@app.route("/accounts", methods=["POST"])
def create_account():
    tree = fromstring(request.data)
    accountCode = tree.find("account_code").text
    find_account_or_404(accountCode) 
    print "creating account %s" % (accountCode)
    Account.save(Account(accountCode))
    return render_template("account.xml", account=Account.find(accountCode)), 201

# not part of the official api, used to manage state in testing
@app.route("/accounts/<accountCode>/billing_method", methods=["POST"])
def post_account_billing_method(accountCode):
    method = request.form['method']
    acc = find_account_or_404(accountCode) 
    acc.billingMethod = method
    Account.save(acc)
    return method, 200

@app.route("/accounts/<accountCode>/billing_info", methods=["GET"])
def get_account_billing_info(accountCode):
    acc = find_account_or_404(accountCode) 
    return render_template("billing_info.xml", account=acc), 200

# PLANS 


def find_plan_or_404(planCode):
    plan = Plan.find(planCode)
    if not plan:
        raise NotFoundError("Couldn't find Plan with plan_code = %s" % planCode)
    return plan


@app.route("/plans", methods=["POST"])
def create_plan():
    tree = fromstring(request.data)
    plan = Plan.fromTree(tree)
    if Plan.find(plan.planCode):
        print "error: Plan:%s already exists" % (plan.planCode)
        return render_template("error.xml", errors=[FieldError('plan', 'plan_code', 'taken')]), 422
    
    print "creating plan %s" % (plan.planCode)
    Plan.save(plan)
    return render_template("plan.xml", plan=plan), 201

@app.route("/plans/<planCode>", methods=["PUT"])
def update_plan(planCode):
    find_plan_or_404(planCode)
    tree = fromstring(request.data)
    plan = Plan.fromTree(tree)
    Plan.save(plan)
    return render_template("plan.xml", plan=plan), 200

@app.route("/plans/<planCode>", methods=["GET"])
def get_plan(planCode):
    plan = find_plan_or_404(planCode)
    return render_template("plan.xml", plan=plan), 200

@app.route("/plans/<planCode>", methods=["DELETE"])
def delete_plan(planCode):
    plan = find_plan_or_404(planCode)
    Plan.delete(plan)
    return "", 204

if __name__ == '__main__':
    app.debug = True
    app.run('0.0.0.0', int(sys.argv[1] if len(sys.argv) > 1 else 5000))
