(function () {
  if (typeof window === "undefined") {
    return;
  }

  const throttle = (fn, wait) => {
    let last = 0;
    return (...args) => {
      const now = Date.now();
      if (now - last >= wait) {
        last = now;
        fn.apply(null, args);
      }
    };
  };

  const formatMoney = (el) => {
    const raw = (el.value || "").trim();
    if (!raw) {
      el.value = "";
      return;
    }
    const numeric = raw.replace(/[^0-9.-]/g, "");
    if (!numeric) {
      el.value = "";
      return;
    }
    const value = Number.parseFloat(numeric);
    if (Number.isFinite(value)) {
      el.value = value.toFixed(2);
    }
  };

  const formatMileage = (el) => {
    const raw = (el.value || "").replace(/[^0-9]/g, "");
    el.value = raw;
  };

  const forms = document.querySelectorAll(
    'form[data-enhanced-form]:not([data-enhanced-bound])'
  );

  const todayIso = new Date().toISOString().split("T")[0];

  forms.forEach((form) => {
    form.dataset.enhancedBound = "1";

    const draftKey =
      form.dataset.draftKey ||
      `draft:${location.pathname}:${
        form.getAttribute("name") || form.id || "form"
      }`;

    // Restore draft
    try {
      const stored = localStorage.getItem(draftKey);
      if (stored) {
        const data = JSON.parse(stored);
        Object.entries(data).forEach(([name, value]) => {
          const field = form.elements.namedItem(name);
          if (!field) return;
          if (field.type === "checkbox" || field.type === "radio") {
            field.checked = Boolean(value);
          } else {
            field.value = value;
          }
        });
      }
    } catch (error) {
      console.warn("Unable to restore draft", error);
    }

    // Formatting hooks
    form.querySelectorAll("[data-money]").forEach((el) => {
      el.addEventListener("blur", () => formatMoney(el));
    });

    form.querySelectorAll("[data-mileage]").forEach((el) => {
      el.addEventListener("input", () => formatMileage(el));
    });

    form.querySelectorAll("[data-date-max-today]").forEach((el) => {
      if (!el.max) {
        el.max = todayIso;
      }
    });

    const saveDraft = throttle(() => {
      try {
        const snapshot = {};
        Array.from(form.elements).forEach((el) => {
          if (!el.name || el.dataset.skipAutosave === "true") {
            return;
          }
          if (el.type === "file") {
            return;
          }
          if (el.type === "checkbox") {
            snapshot[el.name] = el.checked;
          } else {
            snapshot[el.name] = el.value;
          }
        });
        localStorage.setItem(draftKey, JSON.stringify(snapshot));
      } catch (error) {
        console.warn("Unable to store draft", error);
      }
    }, 400);

    form.addEventListener("input", saveDraft);

    form.addEventListener("submit", () => {
      const submitBtn = form.querySelector(
        'button[type="submit"], input[type="submit"]'
      );
      if (submitBtn) {
        submitBtn.disabled = true;
        if (submitBtn.dataset.originalText === undefined) {
          submitBtn.dataset.originalText = submitBtn.textContent;
        }
        if (submitBtn.tagName === "BUTTON") {
          submitBtn.textContent =
            submitBtn.dataset.submittingText || "Saving…";
        }
      }
      localStorage.removeItem(draftKey);
    });
  });

  // Focus first invalid field if present
  const firstInvalid =
    document.querySelector('[aria-invalid="true"]') ||
    document.querySelector(".is-invalid");
  if (firstInvalid && typeof firstInvalid.focus === "function") {
    firstInvalid.focus({ preventScroll: false });
  }
})();
(function () {
  const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));
  const $ = (selector, root = document) => root.querySelector(selector);

  const throttle = (fn, wait = 400) => {
    let last = 0;
    return (...args) => {
      const now = Date.now();
      if (now - last >= wait) {
        last = now;
        fn(...args);
      }
    };
  };

  const formatMoney = (input) => {
    const raw = (input.value || "").replace(/[^0-9.-]/g, "");
    if (!raw) {
      input.value = "";
      return;
    }
    const value = Number(raw);
    if (!Number.isNaN(value)) {
      input.value = value.toFixed(2);
    }
  };

  const normalizeMileage = (input) => {
    const digits = (input.value || "").replace(/[^0-9]/g, "");
    input.value = digits;
  };

  const constrainDate = (input) => {
    if (input.type === "date") {
      return; // browser handles constraints
    }
    input.addEventListener("blur", () => {
      const value = input.value.trim();
      if (!value) return;
      const isoMatch = value.match(/^(\d{4})-(\d{2})-(\d{2})$/);
      if (isoMatch) {
        const [, y, m, d] = isoMatch;
        input.value = `${m}/${d}/${y}`;
      }
    });
  };

  const getDraftKey = (form) => {
    const identifier = form.dataset.formKey || form.id || "anonymous";
    return `draft:${location.pathname}:${identifier}`;
  };

  const loadDraft = (form, draftKey) => {
    try {
      const draft = localStorage.getItem(draftKey);
      if (!draft) return;
      const data = JSON.parse(draft);
      Object.entries(data).forEach(([name, value]) => {
        const field = form.elements.namedItem(name);
        if (!field || field.type === "file") return;
        if (field.type === "checkbox") {
          field.checked = Boolean(value);
        } else if (field.type === "radio") {
          const radio = $$(`input[name="${name}"][value="${value}"]`, form)[0];
          if (radio) radio.checked = true;
        } else {
          field.value = value;
        }
      });
    } catch (error) {
      console.warn("Unable to load form draft", error);
    }
  };

  const bindAutosave = (form, draftKey) => {
    const save = throttle(() => {
      const data = {};
      Array.from(form.elements).forEach((el) => {
        if (!el.name || el.type === "file") return;
        if (el.type === "checkbox") {
          data[el.name] = el.checked;
        } else if (el.type === "radio") {
          if (el.checked) data[el.name] = el.value;
        } else {
          data[el.name] = el.value;
        }
      });
      try {
        localStorage.setItem(draftKey, JSON.stringify(data));
      } catch (error) {
        console.warn("Unable to persist draft", error);
      }
    });

    form.addEventListener("input", save);
    form.addEventListener("change", save);
    form.addEventListener("submit", () => {
      localStorage.removeItem(draftKey);
    });
  };

  const disableOnSubmit = (form) => {
    form.addEventListener("submit", () => {
      const button = form.querySelector('[type="submit"]');
      if (button) {
        button.disabled = true;
        if (!button.dataset.originalText) {
          button.dataset.originalText = button.textContent;
        }
        button.textContent = button.dataset.submittingText || "Saving…";
      }
    });
  };

  const focusFirstError = (form) => {
    const firstError = form.querySelector('[aria-invalid="true"], .is-invalid');
    if (firstError && typeof firstError.focus === "function") {
      setTimeout(() => firstError.focus({ preventScroll: false }), 0);
    }
  };

  const enhanceForms = () => {
    $$('form[data-enhanced-form]:not([data-enhanced-bound])').forEach((form) => {
      form.dataset.enhancedBound = "1";

      const draftKey = getDraftKey(form);
      loadDraft(form, draftKey);
      bindAutosave(form, draftKey);
      disableOnSubmit(form);

      $$('[data-money]', form).forEach((input) => {
        input.addEventListener("blur", () => formatMoney(input));
      });

      $$('[data-mileage]', form).forEach((input) => {
        input.addEventListener("input", () => normalizeMileage(input));
      });

      $$('[data-date]', form).forEach((input) => constrainDate(input));

      if (form.dataset.hasErrors === "true") {
        focusFirstError(form);
      }
    });
  };

  document.addEventListener("DOMContentLoaded", enhanceForms);
  document.addEventListener("account:change", enhanceForms);
})();
