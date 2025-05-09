(* utils.ml *)
let print_all_headers message =
  let print_header (header: (string * string)) =
    let t, c = header in
    Dream.log "%s : %s" t c
  in
  Dream.log "%s" "--- Headers ---";
  List.iter print_header (Dream.all_headers message)