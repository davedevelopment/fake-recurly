from flask import Flask, url_for, request, render_template, redirect
from xml.etree.ElementTree import ElementTree, fromstring
from fakerecurly.models import *
from fakerecurly.errors import *
import time

app = Flask(__name__)

@app.route("/", methods=["DELETE"])
def teardown():
    print "Tearing down data"
    Transaction.truncate()
    Subscription.truncate()
    Account.truncate()
    Plan.truncate()
    return "", 204

@app.errorhandler(NotFoundError)
def resource_not_found(error):
    print "error: %s" % error
    return render_template("error.xml", error=error), 404

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

@app.route("/subscriptions/<uuid>/cancel", methods=["PUT"])
def cancel_subscription(uuid):
    sub = find_subscription_or_404(uuid)
    sub.state = "canceled"
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
    print transactions
    return render_template("transactions.xml", transactions=transactions), 200

@app.route("/accounts", methods=["POST"])
def create_account():
    tree = fromstring(request.data)
    accountCode = tree.find("account_code").text
    find_account_or_404(accountCode) 
    print "creating account %s" % (accountCode)
    Account.save(Account(accountCode))
    return render_template("account.xml", account=Account.find(accountCode)), 201

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
    app.run()
