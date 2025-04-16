(* server.ml *)
module type DB = Caqti_lwt.CONNECTION
module T = Caqti_type


let list_products =
  let query =
    let open Caqti_request.Infix in
    (T.unit ->* T.(t2 int string))
    "SELECT code_saq, name FROM products LIMIT 10" in
  fun (module Db : DB) ->
    let%lwt products_or_error = Db.collect_list query () in
    Caqti_lwt.or_fail products_or_error

  (* let query =
    let open Caqti_request.Infix in
    (T.string ->. T.unit)
    "INSERT INTO comment (text) VALUES ($1)" in
  fun text (module Db : DB) ->
    let%lwt unit_or_error = Db.exec query text in
    Caqti_lwt.or_fail unit_or_error *)

let retrive_single_product =
  let query =
    let open Caqti_request.Infix in
    (T.string ->* T.(t2 int string))
    "SELECT code_saq, name FROM products WHERE code_saq = ($1) LIMIT 10" in
  fun code_saq (module Db : DB) ->
    let%lwt products_or_error = Db.collect_list query code_saq in
    Caqti_lwt.or_fail products_or_error

let bleh (a : int * string) (acc : string) : string =
  let code, name = a in
  acc ^ string_of_int code ^ ": " ^ name ^ "\n"

(* GET /products *)
let get_products = (fun request ->
  let%lwt products = Dream.sql request list_products in
  let text = List.fold_right bleh products "" in
  Dream.html text)

(* GET /products/:code_saq *)
let get_product = (fun request ->
  let%lwt products = 
    Dream.sql request (retrive_single_product (Dream.param request "code_saq")) 
  in
  let text = List.fold_right bleh products "" in
  Dream.html text)

let () =
  (* Uncomment to use the debug error handler *)
  (* Dream.run ~error_handler:Dream.debug_error_handler *)
  Dream.run
  @@ Dream.logger
  @@ Dream.sql_pool "postgresql://postgres:testing@localhost/saq_db"
  @@ Dream.router [

    Dream.get "/"
      (fun request ->
        Dream.log "Sending greeting to %s!" (Dream.client request);
        Dream.html "Good morning, world!");

    Dream.get "/echo/:word"
      (fun request ->
        Dream.html (Dream.param request "word"));

    Dream.get "/products" get_products;

    Dream.get "/products/:code_saq" get_product;
  ]