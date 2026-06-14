import { Navigate, Route, Routes } from "react-router-dom";

import { useMe } from "./api/auth";
import { AuthCallback } from "./pages/AuthCallback";
import { Directory } from "./pages/Directory";
import { Login } from "./pages/Login";
import { MemberDetail } from "./pages/MemberDetail";
import { Profile } from "./pages/Profile";

export function App() {
  const { data: me, isLoading } = useMe();

  if (isLoading) return <div className="container">Loading…</div>;

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/auth/callback" element={<AuthCallback />} />
      {me ? (
        <>
          <Route path="/" element={<Directory />} />
          <Route path="/me" element={<Profile />} />
          <Route path="/members/:id" element={<MemberDetail />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </>
      ) : (
        <Route path="*" element={<Navigate to="/login" replace />} />
      )}
    </Routes>
  );
}
