"use client";

import { X } from "../Icons";
import QuizBuilder from "./QuizBuilder";

/** Test sozlamalari va savollarini kengroq oynada tahrirlash — karta-grid dizaynida
 * QuizBuilder inline akkordeon o'rniga shu yerda ochiladi. */
export default function EditQuizModal({ lesson, onClose, onError }) {
  return (
    <div className="eqm-overlay" onMouseDown={onClose}>
      <div className="card eqm-modal" onMouseDown={(e) => e.stopPropagation()}>
        <div className="row-between">
          <div>
            <h3 style={{ margin: 0 }}>{lesson.title}</h3>
            <p className="small dim" style={{ margin: "2px 0 0" }}>Test sozlamalari va savollari</p>
          </div>
          <button type="button" className="btn btn-ghost btn-sm" onClick={onClose}>
            <X width={15} height={15} />
          </button>
        </div>

        <QuizBuilder quizId={lesson.quiz_id} onError={onError} />
      </div>

      <style jsx>{`
        .eqm-overlay {
          position: fixed;
          inset: 0;
          background: rgba(18, 20, 28, 0.45);
          display: flex;
          align-items: flex-start;
          justify-content: center;
          z-index: 100;
          padding: 40px 16px;
          overflow-y: auto;
        }
        .eqm-modal {
          width: 100%;
          max-width: 720px;
          margin: auto;
        }
      `}</style>
    </div>
  );
}
