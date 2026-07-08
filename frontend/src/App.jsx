import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./Pages/Login";
import Register from "./Pages/Register";
import Browse from "./Pages/Browse";
import Lobby from "./Pages/Lobby";
import Play from "./Pages/Play";
import Result from "./Pages/Result";
import AdminDashboard from "./Pages/AdminDashboard";
import QuizBuilder from "./Pages/QuizBuilder";
import ProtectedRoute from "./components/ProtectedRoute";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/quizzes" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        <Route path="/quizzes" element={<ProtectedRoute><Browse /></ProtectedRoute>} />
        <Route path="/quizzes/:quizId/lobby" element={<ProtectedRoute><Lobby /></ProtectedRoute>} />
        <Route path="/quizzes/:quizId/play" element={<ProtectedRoute role="player"><Play /></ProtectedRoute>} />
        <Route path="/quizzes/:quizId/result" element={<ProtectedRoute role="player"><Result /></ProtectedRoute>} />

        <Route path="/admin" element={<ProtectedRoute role="admin"><AdminDashboard /></ProtectedRoute>} />
        <Route path="/admin/quizzes/new" element={<ProtectedRoute role="admin"><QuizBuilder /></ProtectedRoute>} />
        <Route path="/admin/quizzes/:quizId" element={<ProtectedRoute role="admin"><QuizBuilder /></ProtectedRoute>} />

        <Route path="*" element={<Navigate to="/quizzes" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
