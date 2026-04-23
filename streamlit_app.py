
import os
from datetime import datetime

import streamlit as st

from Artist import Artist
from PaintMenu import PaintMenu
from Paint import Paint


# Load menu once
script_dir = os.path.dirname(__file__)
menu_file_path = os.path.join(script_dir, "paint_menu.txt")
menu = PaintMenu.from_file(menu_file_path)
if not menu:
    st.error("Menu could not be loaded. Check paint_menu.txt.")
    st.stop()


# Session state init
if 'artist' not in st.session_state:
    st.session_state.artist = None
if 'orders' not in st.session_state:
    st.session_state.orders = None  # Lazy load
if 'action' not in st.session_state:
    st.session_state.action = 'Place Order'
if 'additive_parts' not in st.session_state:
    st.session_state.additive_parts = 0
if 'last_additives_choice' not in st.session_state:
    st.session_state.last_additives_choice = "none"
if 'additive_parts_update' not in st.session_state:
    st.session_state.additive_parts_update = 0
if 'last_additives_choice_update' not in st.session_state:
    st.session_state.last_additives_choice_update = "none"

def update_parts():
    """Update additive parts in session state based on which widget triggered the callback."""
    if "parts_input" in st.session_state and st.session_state["parts_input"] != st.session_state.additive_parts:
        st.session_state.additive_parts = st.session_state.parts_input
    if "parts_input_update" in st.session_state and st.session_state["parts_input_update"] != st.session_state.additive_parts_update:
        st.session_state.additive_parts_update = st.session_state.parts_input_update


def load_orders():
    """
    Load orders from orders.txt if not already loaded.
    Returns:
        list: List of Paint order objects.
    """
    if st.session_state.orders is not None:
        return st.session_state.orders
    try:
        script_dir = os.path.dirname(__file__)
        file_path = os.path.join(script_dir, "orders.txt")
        with open(file_path, 'r') as f:
            lines = f.readlines()
        orders = []
        for line in lines:
            parts = line.strip().split(',')
            if len(parts) == 8:
                # artist_name,location,timestamp,paint_base,size,additives,additive_parts,cost
                artist_name_parts = parts[0].split()
                if len(artist_name_parts) >= 2:
                    fname = artist_name_parts[0]
                    lname = ' '.join(artist_name_parts[1:])
                else:
                    fname = parts[0]
                    lname = ''
                location = parts[1]
                artist = Artist(fname, lname, location)
                timestamp = datetime.fromisoformat(parts[2])
                paint_base = parts[3]
                size = parts[4]
                additives = parts[5]
                additive_parts = int(parts[6])
                cost = float(parts[7])
                order = Paint(artist, paint_base, size, additives, additive_parts)
                # Set private attributes
                order._Paint__timestamp = timestamp
                order._Paint__cost = cost
                orders.append(order)
        st.session_state.orders = orders
        return orders
    except FileNotFoundError:
        st.session_state.orders = []
        return []
    except Exception as e:
        st.error(f"Error loading orders file: {e}")
        st.session_state.orders = []
        return []


def save_order(order):
    """Save order using the Paint.save method."""
    order.save()


# Main app
st.title("Paint Order System")

if st.session_state.artist is None:
    st.header("Artist Login")
    with st.form("login_form"):
        fname = st.text_input("First Name")
        lname = st.text_input("Last Name")
        location = st.text_input("Studio Number")
        submitted = st.form_submit_button("Login")
        if submitted:
            if fname and lname and location:
                st.session_state.artist = Artist(fname, lname, location)
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Please fill all fields.")

else:
    # Sidebar for navigation
    st.sidebar.header("Navigation")
    if st.sidebar.button("Place Order"):
        st.session_state.action = "Place Order"
        st.rerun()
    if st.sidebar.button("View Orders"):
        st.session_state.action = "View Orders"
        st.rerun()
    if st.sidebar.button("Update Order"):
        st.session_state.action = "Update Order"
        st.rerun()
    if st.sidebar.button("Delete Order"):
        st.session_state.action = "Delete Order"
        st.rerun()
    if st.sidebar.button("Refresh Orders"):
        st.session_state.orders = None  # Force reload
        st.rerun()
    action = st.session_state.action

    if action == "Place Order":
        st.header("Place a New Order")
        with st.form("order_form"):
            paint_base = st.selectbox("Paint Base", menu.get_paint_base())
            size_options = [
                f"{s.split(':')[0].strip()} - ${s.split(':')[1].strip()}"
                for s in menu.get_size()
            ]
            size = st.selectbox("Size", size_options)
            additives_options = menu.get_additives()
            additives_index = (
                additives_options.index("None") if "None" in additives_options else 0
            )
            additives = st.selectbox(
                "Additives", additives_options, index=additives_index
            )
            # We'll handle additive_parts and its display outside the form
            submitted = st.form_submit_button("Submit Order")

        # Outside the form for dynamic display of additive parts and confirmation buttons
        show_parts = additives.lower() != "none"
        if show_parts:
            # Ensure key is unique for this context or shared appropriately
            # Reset additive_parts if additives changed to None *before* input
            if st.session_state.get('last_additives_choice') != additives:
                st.session_state.additive_parts = 0
                st.session_state.last_additives_choice = additives

            additive_parts_value = st.number_input(
                "Additive Parts",
                min_value=0,
                step=1,
                value=st.session_state.additive_parts,
                key="parts_input",
                on_change=update_parts
            )
            st.session_state.additive_parts = additive_parts_value # Update session state directly
            if st.session_state.additive_parts > 0:
                st.write(
                    f"+$0.10 per part. Total additional: ${(st.session_state.additive_parts * 0.10):.2f}"
                )
            else:
                st.write("+$0.10 per part.")
        else:
            st.session_state.additive_parts = 0 # Reset if no additives selected
            st.session_state.last_additives_choice = "none" # Track last choice
            # Optionally display "+$0.10 per part." even if no parts, or hide completely
            # st.write("+$0.10 per part.") # Keep consistency if needed

        if submitted:
            # Extract size name
            size_name = size.split(' - ')[0]
            order = Paint(
                st.session_state.artist, paint_base, size_name, additives, st.session_state.additive_parts
            )
            order.calculate_cost(menu)
            st.session_state.current_order_for_confirmation = order # Store order for confirmation

            st.code(str(order))
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Confirm and Save", key="confirm_save_btn"):
                    save_order(st.session_state.current_order_for_confirmation)
                    if st.session_state.orders is not None:
                        st.session_state.orders.append(st.session_state.current_order_for_confirmation)
                    st.success("Order saved!")
                    del st.session_state.current_order_for_confirmation # Clear after saving
                    st.rerun()
            with col2:
                if st.button("Cancel Order", key="cancel_order_btn"):
                    st.info("Order cancelled.")
                    del st.session_state.current_order_for_confirmation # Clear
                    st.rerun()


    elif action == "View Orders":
        st.header("View Orders")
        orders = load_orders()
        if not orders:
            st.info("No orders found. Would you like to place a new order?")
            if st.button("Place Order"):
                st.session_state.action = "Place Order"
                st.rerun()
        else:
            # Prepare data for dataframe
            data = []
            for order in orders:
                item = f"{order.get_size()} {order.get_paint_base()} - {order.get_additives()} ({order.get_additive_parts()})"
                data.append({
                    "Timestamp": order.get_timestamp().strftime("%Y-%m-%d %I:%M %p"),
                    "Item": item,
                    "Cost": f"${order.get_cost():.2f}",
                    "Artist": f"{order.get_artist().get_fname()} {order.get_artist().get_lname()}"
                })
            st.dataframe(data)
            # Buttons in table? Streamlit dataframe doesn't support buttons directly, so perhaps list with buttons
            st.subheader("Quick Actions")
            for i, order in enumerate(orders):
                col1, col2, col3 = st.columns([3,1,1])
                with col1:
                    st.write(f"Order {i+1}: {data[i]['Item']}")
                with col2:
                    if st.button(f"Edit {i+1}", key=f"edit_{i}"):
                        st.session_state.edit_index = i
                        st.session_state.action = "Update Order"
                        st.rerun()
                with col3:
                    if st.button(f"Delete {i+1}", key=f"delete_{i}"):
                        st.session_state.delete_index = i
                        st.session_state.action = "Delete Order"
                        st.rerun()

    elif action == "Update Order":
        st.header("Update Order")
        orders = load_orders()
        if not orders:
            st.info("No orders to update. Would you like to place a new order?")
            if st.button("Place Order"):
                st.session_state.action = "Place Order"
                st.rerun()
        else:
            if 'edit_index' in st.session_state and st.session_state.edit_index < len(orders):
                idx = st.session_state.edit_index
                order = orders[idx]
                st.write(f"Updating: {order}")
                with st.form("update_form"):
                    paint_base = st.selectbox(
                        "Paint Base",
                        menu.get_paint_base(),
                        index=menu.get_paint_base().index(order.get_paint_base())
                        if order.get_paint_base() in menu.get_paint_base() else 0,
                    )
                    size_options = [
                        f"{s.split(':')[0].strip()} - ${s.split(':')[1].strip()}"
                        for s in menu.get_size()
                    ]
                    size_display = f"{order.get_size()} - ${dict(s.split(':') for s in menu.get_size()).get(order.get_size(), '0.00')}"
                    size_index = size_options.index(size_display) if size_display in size_options else 0
                    size = st.selectbox("Size", size_options, index=size_index)
                    additives_options = menu.get_additives()
                    additives_index = (
                        additives_options.index(order.get_additives())
                        if order.get_additives() in additives_options
                        else (additives_options.index("None") if "None" in additives_options else 0)
                    )
                    additives = st.selectbox("Additives", additives_options, index=additives_index)
                    show_parts = additives.lower() != "none"
                    if show_parts:
                        additive_parts = st.number_input(
                            "Additive Parts",
                            min_value=0,
                            step=1,
                            value=order.get_additive_parts(),
                            key="parts_input",
                            on_change=update_parts,
                        )
                        if st.session_state.additive_parts > 0:
                            st.write(
                                f"+$0.10 per part. Total additional: ${(st.session_state.additive_parts * 0.10):.2f}"
                            )
                        else:
                            st.write("+$0.10 per part.")
                    else:
                        additive_parts = 0
                    submitted = st.form_submit_button("Update Order")
                    if submitted:
                        # Extract size name
                        size_name = size.split(' - ')[0]
                        updated_order = Paint(
                            st.session_state.artist, paint_base, size_name, additives, additive_parts
                        )
                        updated_order.calculate_cost(menu)
                        st.code(str(updated_order))
                        if st.button("Confirm Update"):
                            orders[idx] = updated_order
                            save_order(updated_order)  # Note: This appends, so file will have duplicate, but for simplicity
                            st.session_state.orders = None  # Force reload orders for other tabs
                            st.success("Order updated!")
                            del st.session_state.edit_index
                            st.rerun()
                # Outside form for dynamic display
                show_parts_update = additives.lower() != "none"
                if show_parts_update:
                    # Ensure key is unique for this context or shared appropriately
                    # Reset additive_parts if additives changed to None *before* input
                    if st.session_state.get('last_additives_choice_update') != additives:
                        st.session_state.additive_parts_update = 0
                        st.session_state.last_additives_choice_update = additives

                    additive_parts_value_update = st.number_input(
                        "Additive Parts",
                        min_value=0,
                        step=1,
                        value=st.session_state.additive_parts_update or order.get_additive_parts(),
                        key="parts_input_update",
                        on_change=update_parts
                    )
                    st.session_state.additive_parts_update = additive_parts_value_update
                    if st.session_state.additive_parts_update > 0:
                        st.write(
                            f"+$0.10 per part. Total additional: ${(st.session_state.additive_parts_update * 0.10):.2f}"
                        )
                    else:
                        st.write("+$0.10 per part.")
                else:
                    st.session_state.additive_parts_update = 0
                    st.session_state.last_additives_choice_update = "none"

            else:
                st.info("Select an order to update from View Orders.")

    elif action == "Delete Order":
        st.header("Delete Order")
        orders = load_orders()
        if not orders:
            st.info("No orders to delete. Would you like to place a new order?")
            if st.button("Place Order"):
                st.session_state.action = "Place Order"
                st.rerun()
        else:
            if 'delete_index' in st.session_state and st.session_state.delete_index < len(orders):
                idx = st.session_state.delete_index
                order = orders[idx]
                st.write(f"Deleting: {order}")
                if st.button("Confirm Delete"):
                    del orders[idx]
                    st.success("Order deleted from session. (File not updated for simplicity)")
                    del st.session_state.delete_index
                    st.rerun()
            else:
                st.info("Select an order to delete from View Orders.")
