import { Navigate, Outlet, Route, Routes } from "react-router-dom";

import { useMe } from "./api/auth";
import { TopBar } from "./components/TopBar";
import { AuthCallback } from "./pages/AuthCallback";
import { Directory } from "./pages/Directory";
import { Home } from "./pages/Home";
import { Login } from "./pages/Login";
import { MemberDetail } from "./pages/MemberDetail";
import { Profile } from "./pages/Profile";

function AuthedLayout() {
  return (
    <>
      <TopBar />
      <Outlet />
    </>
  );
}

export function App() {
  const { data: me, isLoading } = useMe();

  if (isLoading) return <div className="auth-wrap muted">Loading…</div>;

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/auth/callback" element={<AuthCallback />} />
      {me ? (
        <Route element={<AuthedLayout />}>
          <Route path="/" element={<Home />} />
          <Route path="/directory" element={<Directory />} />
          <Route path="/me" element={<Profile />} />
          <Route path="/members/:id" element={<MemberDetail />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      ) : (
        <Route path="*" element={<Navigate to="/login" replace />} />
      )}
    </Routes>
  );
}
