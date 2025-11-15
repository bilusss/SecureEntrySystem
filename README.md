# SecureEntrySystem

---

## 🛠️ Technologie użyte w projekcie

### 🔹 1. Rozpoznawanie twarzy – `face_recognition` (by ageitgey)
W projekcie **SecureEntrySystem** wykorzystuję bibliotekę  
**`face_recognition` autorstwa ageitgey**, która jest jednym z najpopularniejszych i najłatwiejszych w użyciu narzędzi do rozpoznawania twarzy w Pythonie.

Umożliwia ona:
- generowanie embeddingów twarzy,
- porównywanie twarzy pracownika z obrazem z kamery,
- identyfikację użytkownika w czasie rzeczywistym.

Mechanizm ten pozwala potwierdzić, że osoba skanująca przepustkę jest faktycznym posiadaczem uprawnień.

---

### 🔹 2. Frontend – React (JSX) + Vite + TailwindCSS
Interfejs użytkownika został zbudowany z użyciem:
- **React JSX** – łatwe tworzenie dynamicznych komponentów,
- **Vite** – szybkie środowisko dev i bundler,
- **TailwindCSS** – utility-first framework przyspieszający tworzenie UI.

Frontend będzie obejmował:
- panel administratora,
- przegląd logów wejść,
- moduł zarządzania pracownikami,
- moduł generowania raportów oraz obsługi przepustek QR.

---

### 🔹 3. System QR – identyfikacja pracowników
Do obsługi QR kodów wykorzystywana jest biblioteka:

### 👉 `qrcode` (Python)

Pozwala ona generować kody QR w formacie graficznym, jest stabilna i szeroko stosowana w projektach produkcyjnych.

#### 🔄 Miesięczna rotacja QR kodów
Każdy pracownik posiada **unikalny kod QR**, który:
- jest przypisany do jego identyfikatora w systemie,
- **automatycznie regeneruje się raz w miesiącu**, co zwiększa poziom bezpieczeństwa,
- służy jako przepustka wstępu.

Proces weryfikacji wejścia:
1. Pracownik skanuje kod QR.
2. System sprawdza, czy kod jest ważny i aktualny.
3. W tym samym czasie wykonywane jest rozpoznanie twarzy.
4. Wejście zostaje zaakceptowane tylko, jeśli **obie metody uwierzytelniania** potwierdzą tożsamość pracownika.
