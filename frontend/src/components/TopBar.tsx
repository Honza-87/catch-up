import { useQueryClient } from "@tanstack/react-query";
import { Link, NavLink } from "react-router-dom";

import { logout } from "../api/auth";

export function TopBar() {
  const queryClient = useQueryClient();

  async function onSignOut() {
    await logout();
    await queryClient.invalidateQueries({ queryKey: ["me"] });
  }

  return (
    <header className="app-bar">
      <Link to="/" className="brand">
        <span className="pin" aria-hidden="true" />
        catch-up
      </Link>
      <nav className="nav">
        <NavLink to="/" end className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
          Atlas
        </NavLink>
        <NavLink to="/directory" className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
          Classmates
        </NavLink>
        <NavLink to="/me" className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
          Profile
        </NavLink>
        <button className="secondary" onClick={onSignOut}>
          Sign out
        </button>
      </nav>
    </header>
  );
}
