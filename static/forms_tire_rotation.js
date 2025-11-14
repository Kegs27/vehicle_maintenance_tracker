(function(){
  const fmtTo32nds = (val) => {
    if (!val) return null;
    const s = String(val).trim();
    const frac = s.match(/^(\d+(?:\.\d+)?)\s*\/\s*32/);
    if (frac) return parseFloat(frac[1]);
    const dec = parseFloat(s);
    return isNaN(dec) ? null : dec;
  };

  const byId = (id) => document.getElementById(id);

  const collectTread = () => {
    const codes = ["fl","fr","rl","rr"];
    const trip = ["in","mid","out"];
    const data = {};
    codes.forEach(c => {
      data[c] = {};
      trip.forEach(t => {
        data[c][t] = fmtTo32nds(byId(`td_${c}_${t}`)?.value);
      });
    });
    return data;
  };

  const summarizeTread = (td) => {
    const toS = (n) => (n == null ? "—" : `${n}/32`);
    const row = (c, label) => {
      const r = td[c] || {};
      return `${label}: ${toS(r.in)} | ${toS(r.mid)} | ${toS(r.out)}`;
    };
    return [
      row("fl","FL"),
      row("fr","FR"),
      row("rl","RL"),
      row("rr","RR"),
    ].join("; ");
  };

  const buildTireRotationDescription = (form) => {
    const base = 'Tire Rotation';
    const pattern = form.querySelector('select[name="rotation_pattern"]')?.value || "";
    const customNotes = form.querySelector('input[name="custom_pattern_notes"]')?.value?.trim() || "";
    const mileage = form.querySelector('input[name="mileage"]')?.value || "";
    const notes = form.querySelector('textarea[name="description_notes"]')?.value?.trim() || "";

    const parts = [base];

    const patternLabels = {
      front_to_rear: 'Front-to-back',
      cross: 'Cross pattern',
      five_tire: '5-Tire Rotation',
      custom: 'Custom pattern',
    };

    if (pattern && patternLabels[pattern]) {
      parts.push(`Pattern: ${patternLabels[pattern]}`);
    }

    if (pattern === 'custom' && customNotes) {
      parts.push(`Details: ${customNotes}`);
    }

    if (mileage) {
      parts.push(`${Number(mileage).toLocaleString()} mi`);
    }

    if (notes) {
      parts.push(`Notes: ${notes}`);
    }

    return parts.join(' · ');
  };

  document.addEventListener('DOMContentLoaded', () => {
    const patternSelect = byId('rotation_pattern');
    const customPatternGroup = byId('customPatternGroup');
    const customPatternNotesInput = byId('custom_pattern_notes');

    if (patternSelect && customPatternGroup && customPatternNotesInput) {
      const updateCustomVisibility = () => {
        if (patternSelect.value === 'custom') {
          customPatternGroup.classList.remove('d-none');
        } else {
          customPatternGroup.classList.add('d-none');
          customPatternNotesInput.value = '';
        }
      };

      patternSelect.addEventListener('change', updateCustomVisibility);
      updateCustomVisibility();
    }
  });

  document.addEventListener('change', (e) => {
    if (e.target && e.target.id === 'tr_create_fm') {
      const futureFields = document.querySelectorAll('.tr-fm');
      futureFields.forEach(el => {
        el.classList.toggle('d-none', !e.target.checked);
      });
      
      // If checked, scroll to the first future maintenance field
      if (e.target.checked && futureFields.length > 0) {
        setTimeout(() => {
          const firstField = futureFields[0];
          firstField.scrollIntoView({
            behavior: 'smooth',
            block: 'nearest',
          });
        }, 50);
      }
    }
  });

  document.addEventListener('submit', (e) => {
    const form = e.target.closest('#tireRotationModal form');
    if (!form) return;

    const depths = collectTread();
    const summary = summarizeTread(depths);

    const desc = `${buildTireRotationDescription(form)} | Tread (I/M/O): ${summary}`;
    byId('tr_description_auto').value = desc;
    byId('tr_depths_json').value = JSON.stringify(depths);
  });
})();


