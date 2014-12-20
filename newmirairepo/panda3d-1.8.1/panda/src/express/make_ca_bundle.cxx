// Filename: make_ca_bundle.cxx
// Created by:  drose (07Oct09)
//
////////////////////////////////////////////////////////////////////
//
// PANDA 3D SOFTWARE
// Copyright (c) Carnegie Mellon University.  All rights reserved.
//
// All use of this software is subject to the terms of the revised BSD
// license.  You should have received a copy of this license along
// with this source code in a file named "LICENSE."
//
////////////////////////////////////////////////////////////////////

#include "pandabase.h"
#include "openSSLWrapper.h"
#include <stdio.h>

static const char *source_filename = "ca-bundle.crt";
static const char *target_filename = "ca_bundle_data_src.c";

int
main(int argc, char *argv[]) {
  FILE *fin = fopen(source_filename, "r");
  if (fin == NULL) {
    cerr << "Couldn't open " << source_filename << " for reading.\n";
    return 1;
  }

  // Initialize OpenSSL.
  OpenSSLWrapper::get_global_ptr();

  // We have to be sure and clear the OpenSSL error state before we
  // call this function, or it will get confused.
  ERR_clear_error();
  STACK_OF(X509_INFO) *inf;
  inf = PEM_X509_INFO_read(fin, NULL, NULL, NULL);

  if (!inf) {
    // Could not scan certificates.
    cerr << "Couldn't read PEM file in " << source_filename << "\n";
    return 0;
  }
  
  cerr << "PEM_X509_INFO_read() found " << sk_X509_INFO_num(inf)
       << " entries.\n";

  // Now convert the certificates to DER form.
  stringstream der_stream;

  int cert_count = 0;
  int num_entries = sk_X509_INFO_num(inf);
  for (int i = 0; i < num_entries; i++) {
    X509_INFO *itmp = sk_X509_INFO_value(inf, i);

    if (itmp->x509) {
      X509 *cert = itmp->x509;

      int der_len = i2d_X509(cert, NULL);
      unsigned char *der_buf = new unsigned char[der_len];
      unsigned char *p = der_buf;
      i2d_X509(cert, &p);
      der_stream.write((const char *)der_buf, der_len);
      delete[] der_buf;
      cert_count++;
    }
  }
  sk_X509_INFO_pop_free(inf, X509_INFO_free);

  fclose(fin);

  // Now write the data to the .c file, in a compilable form, similar
  // to bin2c.
  ofstream out;
  Filename target = Filename::text_filename(string(target_filename));
  if (!target.open_write(out)) {
    cerr << "Couldn't open " << target_filename << " for writing.\n";
    return (1);
  }

  der_stream.seekg(0);
  istream &in = der_stream;

  string table_type = "const unsigned char ";
  string length_type = "const int ";
  string table_name = "ca_bundle_data";
  string static_keyword = "static ";
  static const int col_width = 11;

  out << "\n"
      << "/*\n"
      << " * This table was generated by the command:\n"
      << " *\n"
      << " * make_ca_bundle\n"
      << " *\n"
      << " * which is a \"test\" program in the express directory; it reads\n"
      << " * ca-bundle.crt and produces this file.\n"
      << " *\n"
      << " * This file represents the set of well-known certificate authorities\n"
      << " * in DER form, for compiling into OpenSSLWrapper.\n"
      << " */\n\n"
      << static_keyword << table_type << table_name << "[] = {";
  out << hex << setfill('0');
  int count = 0;
  int col = 0;
  unsigned int ch;
  ch = in.get();
  while (!in.fail() && !in.eof()) {
    if (col == 0) {
      out << "\n  ";
    } else if (col == col_width) {
      out << ",\n  ";
      col = 0;
    } else {
      out << ", ";
    }
    out << "0x" << setw(2) << ch;
    col++;
    count++;
    ch = in.get();
  }
  out << "\n};\n\n"
      << static_keyword << length_type << table_name << "_len = " 
      << dec << count << ";\n\n";

  cerr << "Wrote " << cert_count << " certificates to " 
       << target_filename << "\n";
  return 0;
}
