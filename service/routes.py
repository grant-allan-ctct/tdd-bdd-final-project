######################################################################
# Copyright 2016, 2022 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################

# spell: ignore Rofrano jsonify restx dbname
"""
Product Store Service with UI
"""
from flask import jsonify, request, abort
from flask import url_for  # noqa: F401 pylint: disable=unused-import
from service.models import Product, Category
from service.common import status  # HTTP Status Codes
from . import app


######################################################################
# H E A L T H   C H E C K
######################################################################
@app.route("/health")
def healthcheck():
    """Let them know our heart is still beating"""
    return jsonify(status=200, message="OK"), status.HTTP_200_OK


######################################################################
# H O M E   P A G E
######################################################################
@app.route("/")
def index():
    """Base URL for our service"""
    return app.send_static_file("index.html")


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################
def check_content_type(content_type):
    """Checks that the media type is correct"""
    if "Content-Type" not in request.headers:
        app.logger.error("No Content-Type specified.")
        abort(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Content-Type must be {content_type}",
        )

    if request.headers["Content-Type"] == content_type:
        return

    app.logger.error("Invalid Content-Type: %s", request.headers["Content-Type"])
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {content_type}",
    )


######################################################################
# C R E A T E   A   N E W   P R O D U C T
######################################################################
@app.route("/products", methods=["POST"])
def create_products():
    """
    Creates a Product
    This endpoint will create a Product based the data in the body that is posted
    """
    app.logger.info("Request to Create a Product...")
    check_content_type("application/json")

    data = request.get_json()
    app.logger.info("Processing: %s", data)
    product = Product()
    product.deserialize(data)
    product.create()
    app.logger.info("Product with new id [%s] saved!", product.id)

    message = product.serialize()

    location_url = url_for("get_products", product_id=product.id, _external=True)
    return jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}


######################################################################
# L I S T   A L L   P R O D U C T S
######################################################################

@app.route("/products", methods=["GET"])
def list_products():
    """
    Retrieves a list of all the products, or all which match provided criteria:
    """
    wanted_name = request.args.get('name')
    wanted_category = request.args.get('category')
    if wanted_name is not None:
        app.logger.info(f"Request to retrieve products with name {jsonify(wanted_name)}")
        wanted_products = Product.find_by_name(wanted_name)
    elif wanted_category is not None:
        app.logger.info(f"Request to retrieve products in category {wanted_category}")
        category_enum = getattr(Category, wanted_category.upper())
        wanted_products = Product.find_by_category(category_enum)
    else:
        app.logger.info("Request to retrieve all products")
        wanted_products = Product.all()

    the_list = [product.serialize() for product in wanted_products]
    app.logger.info(f"Sending back {len(the_list)} products")
    return jsonify(the_list), status.HTTP_200_OK


######################################################################
# R E A D   A   P R O D U C T
######################################################################

@app.route("/products/<int:product_id>", methods=["GET"])
def get_products(product_id):  # I would rather call it `get_product`.
    """
    Retrieves a single product
    This endpoint will find the product with the given ID
    """
    app.logger.info(f"Request to retrieve a Product with ID {product_id}")
    found = Product.find(product_id)
    if found is None:
        abort(status.HTTP_404_NOT_FOUND, f"Product with id '{product_id}' was not found.")
    message = found.serialize()
    return jsonify(message), status.HTTP_200_OK


######################################################################
# U P D A T E   A   P R O D U C T
######################################################################

@app.route("/products/<int:product_id>", methods=["PUT"])
def update_products(product_id):
    """
    Update a Product
    This endpoint will update the product with the given ID, based on the body given
    """
    app.logger.info("Request to update Product with ID [%s]", product_id)
    check_content_type("application/json")

    found = Product.find(product_id)
    if found is None:
        abort(status.HTTP_404_NOT_FOUND, f"Product with id '{product_id}' was not found.")

    data = request.get_json()
    app.logger.info("Processing: %s", data)
    found.deserialize(data)
    found.id = product_id  # deserialize doesn't include the ID
    found.update()
    message = found.serialize()
    return jsonify(message), status.HTTP_200_OK


######################################################################
# D E L E T E   A   P R O D U C T
######################################################################

@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    """
    Delete a Product
    This endpoint will delete the product with the given ID
    """
    app.logger.info(f"Request to delete Product with ID {product_id}")
    our_victim = Product.find(product_id)
    if our_victim:
        our_victim.delete()
    else:
        app.logger.info(f"Product with ID {product_id} was not found")
    return "", status.HTTP_204_NO_CONTENT
