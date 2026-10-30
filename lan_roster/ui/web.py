import threading
from typing import Any, Dict
from flask import Flask, jsonify, redirect, render_template_string, request, url_for
from lan_roster import __version__
from lan_roster.domain.exceptions import InvalidSubnetException
from lan_roster.ui.templates import HTML_DASHBOARD_TEMPLATE
from lan_roster.use_cases.get_devices import GetDevicesUseCase
from lan_roster.use_cases.update_subnet import UpdateSubnetUseCase


def create_web_app(
    get_devices_use_case: GetDevicesUseCase,
    update_subnet_use_case: UpdateSubnetUseCase,
    scan_trigger: threading.Event,
) -> Flask:
    """Factory creating the Flask web presentation adapter."""
    app = Flask(__name__)

    @app.route("/", methods=["GET"])
    def index():
        devices, state = get_devices_use_case.execute()
        return render_template_string(
            HTML_DASHBOARD_TEMPLATE,
            devices=devices,
            state=state,
            error=state.error_message,
            version=__version__,
        )

    @app.route("/scan", methods=["POST"])
    def trigger_scan():
        raw_subnet = request.form.get("subnet", "").strip()
        try:
            update_subnet_use_case.execute(raw_subnet)
            scan_trigger.set()
        except InvalidSubnetException:
            pass  # Error is recorded in state
        return redirect(url_for("index"))

    @app.route("/api/devices", methods=["GET"])
    def api_devices():
        devices, state = get_devices_use_case.execute()
        devices_dict: Dict[str, Any] = {
            ip: dev.to_dict() for ip, dev in devices.items()
        }
        return jsonify({
            "version": __version__,
            "devices": devices_dict,
            "state": state.to_dict(),
        })

    @app.route("/api/set-subnet", methods=["POST"])
    def api_set_subnet():
        data = request.get_json(silent=True) or {}
        raw_subnet = data.get("subnet", "").strip()
        if not raw_subnet:
            return jsonify({"error": "Missing subnet"}), 400

        try:
            normalized = update_subnet_use_case.execute(raw_subnet)
            scan_trigger.set()
            return jsonify({"success": True, "subnet": normalized})
        except InvalidSubnetException as e:
            return jsonify({"error": str(e)}), 400

    return app

