type LogoutListener = () => void;

const logoutListeners = new Set<LogoutListener>();

export function subscribeToLogout(
  listener: LogoutListener,
) {
  logoutListeners.add(listener);

  return () => {
    logoutListeners.delete(listener);
  };
}

export function emitLogout() {
  logoutListeners.forEach((listener) =>
    listener(),
  );
}