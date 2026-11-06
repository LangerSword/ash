import type { DeviceSnapshot, ServiceInfo } from "./types";

export type StepState = "ok" | "working" | "action" | "fail" | "idle";
export type StepAction = "start_board" | "udev" | "retry";

export type Step = {
  key: string;
  label: string;
  state: StepState;
  detail: string;
  action?: { kind: StepAction; label: string };
};

export type Connection = {
  steps: Step[];
  ready: boolean;
  transient: boolean;
  headline: string;
  hint: string;
};

export function connection(
  device: DeviceSnapshot | null,
  service: ServiceInfo | null,
  udevOk: boolean,
): Connection {
  const d = device?.state ?? "starting";
  const steps: Step[] = [];

  // 1. the cable
  const usb: Step = {
    key: "usb",
    label: "USB link",
    state: d === "starting" ? "working" : "idle",
    detail: d === "starting" ? "looking for the board" : "not connected",
  };
  if (d === "ready" || d === "forwarded") {
    usb.state = "ok";
    usb.detail = device?.serial ? `UNO Q ${device.serial}` : "board found";
  } else if (d === "unauthorized") {
    usb.state = "action";
    usb.detail = "USB debugging is not authorised on the board";
  } else if (d === "error") {
    usb.state = "fail";
    usb.detail = device?.detail || "adb could not reach the board";
  } else if (d === "absent") {
    usb.state = "action";
    usb.detail = "no board on USB";
  }
  steps.push(usb);

  // 2. the board's app (the thing that actually answers on 8080)
  const app: Step = {
    key: "app",
    label: "Board app",
    state: "idle",
    detail: "waiting for the USB link",
  };
  if (d === "ready") {
    app.state = "ok";
    app.detail = "answering on the forwarded port";
  } else if (d === "forwarded") {
    app.state = "working";
    app.detail = "not answering yet — starting it";
    app.action = { kind: "start_board", label: "Start board app" };
  } else if (d === "absent" || d === "unauthorized") {
    app.detail = "blocked by the USB link";
  } else if (d === "error") {
    app.detail = "blocked by adb";
  }
  steps.push(app);

  // 3. the local service (seal/unseal/ledger live here)
  const svc: Step = {
    key: "service",
    label: "Local service",
    state: "idle",
    detail: "not started",
  };
  if (service?.mode === "attached" || service?.mode === "spawned") {
    svc.state = "ok";
    svc.detail = `${service.mode} · ${service.base.replace("http://127.0.0.1", "")}`;
  } else if (service?.mode === "starting") {
    svc.state = "working";
    svc.detail = "booting";
  } else if (service?.mode === "unavailable") {
    svc.state = "fail";
    svc.detail = service.detail || "unavailable";
    svc.action = { kind: "retry", label: "Retry" };
  }
  steps.push(svc);

  // 4. permissions, only when they are actually missing
  if (!udevOk) {
    steps.push({
      key: "udev",
      label: "USB permissions",
      state: "action",
      detail: "rule missing — adb may need root",
      action: { kind: "udev", label: "Install rule" },
    });
  }

  const ready = d === "ready" && (service?.mode === "attached" || service?.mode === "spawned");
  const transient = d === "starting" || d === "forwarded" || service?.mode === "starting";

  let headline = "Connecting to the board";
  let hint = "";
  if (ready) {
    headline = "Board connected";
    hint = "";
  } else if (d === "absent") {
    headline = "No board on USB";
    hint = "Plug the UNO Q in. The app picks it up within two seconds.";
  } else if (d === "unauthorized") {
    headline = "Authorise this computer";
    hint = "On the board, tap Allow for USB debugging, then replug.";
  } else if (d === "forwarded") {
    headline = "Starting the board app";
    hint = "This takes a few seconds the first time. It starts on its own.";
  } else if (d === "error") {
    headline = "adb cannot reach the board";
    hint = device?.detail || "Replug the board, then retry.";
  } else if (service?.mode === "unavailable") {
    headline = "Local service is down";
    hint = service.detail || "Restart the app.";
  }

  return { steps, ready, transient, headline, hint };
}
