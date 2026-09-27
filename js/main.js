(function () {
  "use strict";

  // Mobile nav toggle
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.querySelector(".main-nav");
  var siteHeader = document.querySelector(".site-header");
  if (toggle && nav) {
    var setOpen = function (isOpen) {
      if (isOpen && siteHeader) {
        // Panel starts right under the header, wherever it currently is (topbar may be visible).
        var bottom = Math.max(0, siteHeader.getBoundingClientRect().bottom);
        nav.style.setProperty("--nav-top", bottom + "px");
      }
      nav.classList.toggle("open", isOpen);
      toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
      document.body.style.overflow = isOpen ? "hidden" : "";
    };
    toggle.addEventListener("click", function () {
      setOpen(!nav.classList.contains("open"));
    });
    nav.querySelectorAll("a").forEach(function (a) {
      a.addEventListener("click", function () { setOpen(false); });
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && nav.classList.contains("open")) { setOpen(false); toggle.focus(); }
    });
    window.addEventListener("resize", function () {
      if (window.innerWidth > 860 && nav.classList.contains("open")) setOpen(false);
    });
  }

  // Highlight current page in nav (clean, extension-less URLs, e.g. /about)
  var here = location.pathname.replace(/\.html$/i, "").replace(/\/+$/, "").split("/").pop() || "index";
  document.querySelectorAll(".main-nav a[data-page]").forEach(function (a) {
    if (a.getAttribute("data-page") === here) a.classList.add("is-active");
  });

  // Back-to-top button
  var toTop = document.querySelector(".to-top");
  if (toTop) {
    window.addEventListener("scroll", function () {
      toTop.classList.toggle("visible", window.scrollY > 480);
    }, { passive: true });
    toTop.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  // Header shadow on scroll
  var header = document.querySelector(".site-header");
  if (header) {
    var onScroll = function () {
      header.style.boxShadow = window.scrollY > 6 ? "0 6px 20px rgba(16,32,58,.08)" : "none";
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }
})();
