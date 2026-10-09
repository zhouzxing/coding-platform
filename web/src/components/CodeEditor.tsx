import React, { useEffect, useRef } from "react";
import { basicSetup } from "codemirror";
import { EditorView } from "@codemirror/view";
import { oneDark } from "@codemirror/theme-one-dark";
import { EditorState } from "@codemirror/state";
import { python } from "@codemirror/lang-python";

interface Props {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  readOnly?: boolean;
}

export default function CodeEditor({ value, onChange, readOnly }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const viewRef = useRef<EditorView | null>(null);
  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;

  useEffect(() => {
    if (!ref.current) return;
    const state = EditorState.create({
      doc: value,
      extensions: [
        basicSetup,
        python(),
        oneDark,
        EditorView.updateListener.of((u) => {
          if (u.docChanged) onChangeRef.current(u.state.doc.toString());
        }),
      ],
    });
    const view = new EditorView({
      state,
      parent: ref.current,
    });
    viewRef.current = view;
    // Expose globally for external programmatic access (testability)
    (window as any).__cmEditors = (window as any).__cmEditors || [];
    (window as any).__cmEditors.push(view);
    return () => { view.destroy(); };
  }, []);

  // Sync external value -> editor when value changes externally (e.g. reset)
  useEffect(() => {
    const view = viewRef.current;
    if (!view) return;
    const cur = view.state.doc.toString();
    if (cur !== value) {
      const tr = view.state.update({ changes: { from: 0, to: cur.length, insert: value } });
      view.dispatch(tr);
    }
  }, [value]);

  return <div className="code-host" ref={ref} />;
}
